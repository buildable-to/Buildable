# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Source Manager - Manage drawing scripts in a pages/ directory.

Drawing scripts are stored as Python files in a pages/ directory:
  {doc_stem}/pages/*.py

All *.py files are sorted (underscore-prefix first, then alphabetically)
and executed together as one script. Users control file naming and organization.

This provides version-controllable, per-file source of truth.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

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


def _page_sort_key(path: Path) -> tuple:
    """Sort key: underscore-prefixed files first, then alphabetical.

    This ensures files like _helpers.py execute before 001_cover.py,
    matching the common convention of putting shared code in
    underscore-prefixed files.
    """
    name = path.name
    return (0, name) if name.startswith("_") else (1, name)


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
    """List all script files in execution order.

    Returns all *.py files sorted with underscore-prefixed files first,
    then remaining files alphabetically. This means:
    - _helpers.py, _shared.py execute first
    - 001_cover.py, 002_plan.py execute in numeric order
    - foundation.py, notes.py execute alphabetically

    Returns:
        Sorted list of Path objects for each .py file.
    """
    pages_dir = get_pages_dir()
    if not pages_dir or not pages_dir.exists():
        return []
    return sorted(pages_dir.glob("*.py"), key=_page_sort_key)


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
    """Read all scripts concatenated in execution order.

    All *.py files in pages/ are sorted (underscore-prefix first,
    then alphabetically) and concatenated with file boundary markers.

    Returns:
        Combined source code string.
    """
    pages_dir = get_pages_dir()
    if not pages_dir or not pages_dir.exists():
        return ""

    parts = []
    for page_path in list_pages():
        content = read_page(page_path)
        if content.strip():
            parts.append(f"# --- {page_path.name} ---\n{content}")

    return "\n\n".join(parts)


def list_pages_metadata() -> List[Dict[str, Any]]:
    """Get metadata for all scripts (for context building).

    Returns list of dicts with:
        - filename: str
        - path: str (absolute path)
        - line_count: int
        - first_comment: str (first descriptive # comment)
        - has_techdraw: bool
        - has_spreadsheet: bool
    """
    return [_get_page_metadata(p) for p in list_pages()]


def _get_page_metadata(page_path: Path) -> Dict[str, Any]:
    """Extract metadata from a single page file."""
    content = read_page(page_path)
    lines = content.split("\n")

    # Find first descriptive comment (skip boilerplate headers)
    first_comment = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# Page:") or stripped.startswith("# Drawing:"):
            first_comment = stripped.lstrip("# ").strip()
            break
        if stripped.startswith("#") and not any(
            kw in stripped.lower()
            for kw in ["freecad", "created:", "spdx", "encoding", "!/"]
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
    """Initialize the pages/ directory.

    Creates the directory if it doesn't exist. Does not create any
    boilerplate files -- the user controls project structure.

    Returns:
        True if created or already exists, False on error.
    """
    pages_dir = get_pages_dir()
    if not pages_dir:
        return False

    try:
        pages_dir.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        FreeCAD.Console.PrintWarning(f"SourceManager: Failed to init pages/: {e}\n")
        return False


def exists() -> bool:
    """Check if pages/ directory exists."""
    pages_dir = get_pages_dir()
    if not pages_dir:
        return False
    return pages_dir.exists()


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
    for filename in sorted(
        _pages_backup.keys(),
        key=lambda n: (0, n) if n.startswith("_") else (1, n),
    ):
        content = _pages_backup[filename]
        if content.strip():
            parts.append(f"# --- {filename} ---\n{content}")

    return "\n\n".join(parts) if parts else ""


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
# Change detection (for incremental execution)
# =============================================================================


def get_changed_pages() -> Tuple[List[str], List[str], List[str]]:
    """Compare current page files on disk against backup.

    Returns:
        Tuple of (modified, added, deleted) filename lists.
        - modified: file exists in both, content differs
        - added: file on disk but not in backup (Claude created it)
        - deleted: file in backup but not on disk (Claude deleted it)
        Returns ([], [], []) if no backup exists.
    """
    if _pages_backup is None:
        return [], [], []

    pages_dir = get_pages_dir()
    if not pages_dir or not pages_dir.exists():
        return [], [], []

    modified = []
    added = []

    current_files = {f.name for f in pages_dir.glob("*.py")}

    for py_file in pages_dir.glob("*.py"):
        name = py_file.name
        if name in _pages_backup:
            try:
                current = py_file.read_text(encoding="utf-8")
            except Exception:
                continue
            if current != _pages_backup[name]:
                modified.append(name)
        else:
            added.append(name)

    deleted = [name for name in _pages_backup if name not in current_files]

    return modified, added, deleted


def list_helper_pages() -> List[Path]:
    """List underscore-prefixed helper files (shared code).

    These are executed before the target page in incremental mode
    to provide shared variables and functions.

    Returns:
        Sorted list of Path objects for _-prefixed .py files.
    """
    pages_dir = get_pages_dir()
    if not pages_dir or not pages_dir.exists():
        return []
    return sorted(
        (f for f in pages_dir.glob("*.py") if f.name.startswith("_")),
        key=_page_sort_key,
    )


def page_sort_key_str(name: str) -> tuple:
    """Sort key for filename strings (same logic as _page_sort_key for Paths)."""
    return (0, name) if name.startswith("_") else (1, name)


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
