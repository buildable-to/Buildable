# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Source Manager - Manage per-page drawing scripts for multi-page drawing sets.

Drawing pages are stored as individual Python scripts in a pages/ directory:
  {doc_stem}/pages/_shared.py        — Shared constants, executed first
  {doc_stem}/pages/001_cover.py      — First drawing sheet
  {doc_stem}/pages/002_notes.py      — Second drawing sheet
  ...

All pages are executed in sorted order with a shared namespace.
This provides version-controllable, per-page source of truth.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import FreeCAD


# Backup of all page files before Claude edits them
# Maps filename -> content for every .py file in pages/
_pages_backup: Optional[Dict[str, str]] = None

# Document observer instance (set on module load)
_observer = None


class _SourceManagerObserver:
    """Document observer that creates pages/ directory when document is saved."""

    def slotStartSaveDocument(self, doc, filename):
        """Called when document save begins - ensure pages/ directory exists."""
        file_path = Path(filename)
        project_dir = file_path.parent / file_path.stem
        pages_dir = project_dir / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)

        shared_path = pages_dir / "_shared.py"
        if not shared_path.exists():
            _init_shared_file(shared_path, doc.Name)


def _register_observer():
    """Register the document observer if not already registered."""
    global _observer

    if _observer is not None:
        return

    _observer = _SourceManagerObserver()
    FreeCAD.addDocumentObserver(_observer)
    FreeCAD.Console.PrintMessage("SourceManager: Document observer registered\n")


def _unregister_observer():
    """Unregister the document observer."""
    global _observer

    if _observer is None:
        return

    try:
        FreeCAD.removeDocumentObserver(_observer)
    except Exception:
        pass
    _observer = None


# Auto-register observer on module load
_register_observer()


def _init_shared_file(shared_path: Path, doc_name: str) -> None:
    """Create _shared.py with boilerplate."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    shared_path.write_text(
        f"# FreeCAD Drawing Project - {doc_name}\n"
        f"# Created: {timestamp}\n"
        "#\n"
        "# Shared constants and helpers for all pages.\n"
        "# This file is executed first; its variables are available to all page scripts.\n"
        "#\n"
        "\n"
        "import FreeCAD\n"
        "import Draft\n"
        "import math\n"
        "\n"
        'doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("Drawing")\n'
        "\n"
        "# === Project Constants ===\n"
        "# Add shared dimensions, grid spacing, material specs here.\n"
        "# Example:\n"
        "# GRID_SPACING_X = 6000  # mm\n"
        "# GRID_SPACING_Y = 6000  # mm\n"
        '# CONCRETE_CLASS = "C25/30"\n'
        '# REBAR_GRADE = "A500c"\n',
        encoding="utf-8",
    )
    FreeCAD.Console.PrintMessage(f"SourceManager: Initialized {shared_path.name}\n")


# =============================================================================
# Path helpers
# =============================================================================


def get_pages_dir() -> Optional[Path]:
    """Get path to pages/ directory for active document.

    Returns:
        Path to {project_dir}/pages/, or None if document not saved.
    """
    doc = FreeCAD.ActiveDocument
    if not doc or not doc.FileName:
        return None

    doc_path = Path(doc.FileName)
    return doc_path.parent / doc_path.stem / "pages"


def list_pages() -> List[Path]:
    """List all page files in execution order.

    Returns pages sorted by filename (numeric prefix ensures order).
    Excludes _shared.py (it's a dependency, not a page).

    Returns:
        Sorted list of Path objects for each page .py file.
    """
    pages_dir = get_pages_dir()
    if not pages_dir or not pages_dir.exists():
        return []
    return sorted(pages_dir.glob("[0-9]*.py"))


def get_shared_path() -> Optional[Path]:
    """Get path to _shared.py constants file.

    Returns:
        Path to {pages_dir}/_shared.py, or None if not saved.
    """
    pages_dir = get_pages_dir()
    if not pages_dir:
        return None
    return pages_dir / "_shared.py"


# =============================================================================
# Reading
# =============================================================================


def read_page(page_path: Path) -> str:
    """Read a single page file.

    Args:
        page_path: Absolute path to the page .py file.

    Returns:
        File content as string, or empty string on error.
    """
    try:
        return page_path.read_text(encoding="utf-8")
    except Exception:
        return ""


def read_all_pages() -> str:
    """Read _shared.py + all pages concatenated in order.

    Used for full document execution. Concatenates:
    1. _shared.py (if exists)
    2. Each page file in numeric order

    Sections are separated by comments indicating the file boundary.

    Returns:
        Combined source code string.
    """
    pages_dir = get_pages_dir()
    if not pages_dir or not pages_dir.exists():
        return ""

    parts = []

    # 1. _shared.py first
    shared = pages_dir / "_shared.py"
    if shared.exists():
        content = read_page(shared)
        if content.strip():
            parts.append(f"# --- _shared.py ---\n{content}")

    # 2. All numbered pages in order
    for page_path in list_pages():
        content = read_page(page_path)
        if content.strip():
            parts.append(f"\n# --- {page_path.name} ---\n{content}")

    return "\n".join(parts)


def list_pages_metadata() -> List[Dict[str, Any]]:
    """Get metadata for all pages (for context building).

    Returns list of dicts with:
        - filename: str (e.g., "004_foundation_plan.py")
        - path: str (absolute path)
        - line_count: int
        - first_comment: str (first # comment after header, used as description)
        - has_techdraw: bool
        - has_spreadsheet: bool
    """
    pages_dir = get_pages_dir()
    if not pages_dir or not pages_dir.exists():
        return []

    result = []

    # Include _shared.py
    shared = pages_dir / "_shared.py"
    if shared.exists():
        result.append(_get_page_metadata(shared))

    # Include numbered pages
    for page_path in list_pages():
        result.append(_get_page_metadata(page_path))

    return result


def _get_page_metadata(page_path: Path) -> Dict[str, Any]:
    """Extract metadata from a single page file."""
    content = read_page(page_path)
    lines = content.split("\n")

    # Find first descriptive comment (skip header boilerplate)
    first_comment = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# Page:") or stripped.startswith("# Drawing:"):
            first_comment = stripped.lstrip("# ").strip()
            break
        # Skip standard boilerplate comments
        if stripped.startswith("#") and not any(
            kw in stripped.lower()
            for kw in ["freecad", "created:", "shared", "script", "run in", "constants", "example"]
        ):
            first_comment = stripped.lstrip("# ").strip()
            break

    return {
        "filename": page_path.name,
        "path": str(page_path),
        "line_count": len(lines),
        "first_comment": first_comment,
        "has_techdraw": "TechDraw" in content,
        "has_spreadsheet": "Spreadsheet" in content,
    }


# =============================================================================
# Initialization
# =============================================================================


def init_pages_dir() -> bool:
    """Initialize the pages/ directory with _shared.py boilerplate.

    Called on document save if pages/ doesn't exist.

    Returns:
        True if created or already exists, False on error.
    """
    pages_dir = get_pages_dir()
    if not pages_dir:
        return False

    try:
        pages_dir.mkdir(parents=True, exist_ok=True)
        shared = pages_dir / "_shared.py"
        if not shared.exists():
            doc_name = FreeCAD.ActiveDocument.Name if FreeCAD.ActiveDocument else "Drawing"
            _init_shared_file(shared, doc_name)
        return True
    except Exception as e:
        FreeCAD.Console.PrintWarning(f"SourceManager: Failed to init pages/: {e}\n")
        return False


def exists() -> bool:
    """Check if pages/ directory exists with _shared.py."""
    pages_dir = get_pages_dir()
    if not pages_dir:
        return False
    return (pages_dir / "_shared.py").exists()


# =============================================================================
# Backup / Restore for Direct Source Editing
# =============================================================================


def backup_pages() -> bool:
    """Backup ALL files in pages/ before Claude edits.

    Stores a complete snapshot of every .py file in pages/ directory.
    This enables:
    1. Full restore on cancel
    2. Diff between old and new state

    Returns:
        True if backed up successfully.
    """
    global _pages_backup

    pages_dir = get_pages_dir()
    if not pages_dir or not pages_dir.exists():
        _pages_backup = None
        return False

    try:
        _pages_backup = {}
        for py_file in pages_dir.glob("*.py"):
            _pages_backup[py_file.name] = py_file.read_text(encoding="utf-8")

        FreeCAD.Console.PrintMessage(
            f"SourceManager: Backed up {len(_pages_backup)} page files\n"
        )
        return True
    except Exception as e:
        FreeCAD.Console.PrintWarning(f"SourceManager: Backup failed: {e}\n")
        _pages_backup = None
        return False


def restore_pages() -> bool:
    """Restore ALL pages/ files from backup (on cancel).

    1. Delete any NEW files (files in pages/ not in backup)
    2. Restore modified files to backup content
    3. Recreate deleted files from backup

    Returns:
        True if restored successfully.
    """
    global _pages_backup

    if _pages_backup is None:
        return False

    pages_dir = get_pages_dir()
    if not pages_dir:
        _pages_backup = None
        return False

    try:
        # Delete files that were NOT in backup (Claude created them)
        for py_file in pages_dir.glob("*.py"):
            if py_file.name not in _pages_backup:
                py_file.unlink()
                FreeCAD.Console.PrintMessage(
                    f"SourceManager: Deleted new file {py_file.name}\n"
                )

        # Restore all backed-up files
        for filename, content in _pages_backup.items():
            (pages_dir / filename).write_text(content, encoding="utf-8")

        FreeCAD.Console.PrintMessage(
            f"SourceManager: Restored {len(_pages_backup)} page files from backup\n"
        )
        _pages_backup = None
        return True
    except Exception as e:
        FreeCAD.Console.PrintWarning(f"SourceManager: Restore failed: {e}\n")
        return False


def get_backup_combined() -> Optional[str]:
    """Get concatenated backup content for diff preview.

    Returns:
        Combined backup source (same format as read_all_pages()),
        or None if no backup.
    """
    if _pages_backup is None:
        return None

    parts = []

    # _shared.py first
    if "_shared.py" in _pages_backup:
        content = _pages_backup["_shared.py"]
        if content.strip():
            parts.append(f"# --- _shared.py ---\n{content}")

    # Numbered pages in sorted order
    page_files = sorted(
        fn for fn in _pages_backup if fn != "_shared.py" and fn[0].isdigit()
    )
    for filename in page_files:
        content = _pages_backup[filename]
        if content.strip():
            parts.append(f"\n# --- {filename} ---\n{content}")

    return "\n".join(parts) if parts else ""


def clear_backup():
    """Clear backup after successful approve."""
    global _pages_backup
    _pages_backup = None
    FreeCAD.Console.PrintMessage("SourceManager: Cleared backup\n")


def has_backup() -> bool:
    """Check if there's an active backup."""
    return _pages_backup is not None


def get_backup_content() -> Optional[str]:
    """Backward compat alias for get_backup_combined()."""
    return get_backup_combined()


# =============================================================================
# Legacy compat — methods that DrawingPanel may still reference
# =============================================================================


def read_source() -> str:
    """Backward compat alias for read_all_pages()."""
    return read_all_pages()


def backup_source() -> bool:
    """Backward compat alias for backup_pages()."""
    return backup_pages()


def restore_source() -> bool:
    """Backward compat alias for restore_pages()."""
    return restore_pages()
