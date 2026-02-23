# Project Context — Persistent Knowledge Base per Project

## Overview

Every session starts blind — the engineer re-explains loads, materials, naming conventions each time. Project Context gives the AI persistent project knowledge via:

1. **Project notes** — plain text with company conventions, materials, naming rules, title block info
2. **Reference documents** — PDFs (calc sheets, soil reports, floor plans) that Claude reads on-demand

Saved to disk as `project.md` + `reference_docs/` folder. Injected into the system prompt each session.

## User Flow

```
User clicks "Context" button in header
         │
         ▼
┌──────────────────────────────────────┐
│  PROJECT NOTES                       │
│ ┌──────────────────────────────────┐ │
│ │ C25/30 concrete, B500B rebar     │ │  ← QPlainTextEdit, auto-saves
│ │ 40mm cover, 12mm stirrups        │ │    after 2s debounce
│ │ Foundations = FS-XX              │ │
│ └──────────────────────────────────┘ │
│                                      │
│  REFERENCE DOCUMENTS          + Add  │
│ ┌──────────────────────────────────┐ │
│ │ ┌─────────────────┐ ┌─────────┐ │ │
│ │ │ calcs.pdf 2.1MB ×│ │soil ×   │ │ │  ← file chips with remove
│ │ └─────────────────┘ └─────────┘ │ │
│ └──────────────────────────────────┘ │
│        Changes are saved automatically │
└──────────────────────────────────────┘
```

## Architecture

### On-Disk Storage

```
MyProject/
├── MyProject.FCStd
└── MyProject/                     # Project directory
    ├── project.md                 # Engineer's notes (plain text)
    ├── reference_docs/            # Uploaded PDFs, images, specs
    │   ├── structural_calcs.pdf
    │   └── soil_report.pdf
    ├── pages/                     # Drawing scripts
    ├── CLAUDE.md                  # Auto-generated Claude instructions
    └── ...
```

### Three-Tier Instruction System

```
┌─────────────────────────────────────────────────┐
│ System Prompt (FREECAD_SYSTEM_PROMPT_TEMPLATE)  │  Universal drawing rules
│  + Project Notes (from project.md)              │  Engineer's conventions
│  + Reference Documents listing                  │  Available PDFs to read
├─────────────────────────────────────────────────┤
│ CLAUDE.md (project_claude_template.md)          │  Per-project code conventions
├─────────────────────────────────────────────────┤
│ User message + document context                 │  Current request
└─────────────────────────────────────────────────┘
```

## UI: Header Toggle Button

Project Context is accessed via a checkable "Context" button in the Drawing panel header bar, next to Sessions and Settings. This positions it as a Drawing panel feature, not a top-level mode.

```
[3D BETA] [Drawing]          Context  Sessions  ...  Clear
                               ↑
                          Toggle button (checkable)
                          Blue text + dark bg when active
```

**Widget**: `ProjectContextWidget` — full-panel view that replaces the chat via `QStackedWidget`:
- Stack index 0 = `ChatWidget` (drawing mode)
- Stack index 1 = `ProjectContextWidget` (context mode)

**Toggle handler** (`DrawingPanel._on_context_toggled`):
```python
def _on_context_toggled(self, checked: bool):
    if checked:
        self._update_project_dir()  # Refresh from active document
    self._stack.setCurrentIndex(1 if checked else 0)
```

The `_update_project_dir()` call ensures the context view picks up documents saved after the panel was created.

## ProjectContextWidget

**File**: `widgets/project_context.py`

### Components

| Component | Widget | Purpose |
|-----------|--------|---------|
| Notes editor | `QPlainTextEdit` | Free-text project notes, stretch=1 fills available space |
| Docs header | `QHBoxLayout` | "REFERENCE DOCUMENTS" label + "+ Add" button |
| File chips | `_FlowLayout` in `QScrollArea` | Compact chips showing filename, size, × remove button |
| Empty state | `QLabel` | "Drop PDFs, drawings, or specifications here" |
| Auto-save hint | `QLabel` | "Changes are saved automatically" |

### Signals

- `contextChanged` — emitted when notes are saved or file list changes

### Key Methods

| Method | Description |
|--------|-------------|
| `set_project_dir(path)` | Load project.md text + scan reference_docs/ |
| `get_notes_text()` | Return current notes text |
| `get_reference_docs()` | Return list of Path objects in reference_docs/ |
| `_save_notes()` | Write text area to project.md (2s debounce) |
| `_add_document()` | File dialog → copy to reference_docs/ |
| `_remove_document(path)` | Delete file from reference_docs/ |
| `_refresh_file_list()` | Re-scan reference_docs/ and rebuild chip widgets |

### Auto-Save

Notes auto-save via a 2-second debounce timer:
```python
self._save_timer = QTimer(self)
self._save_timer.setSingleShot(True)
self._save_timer.setInterval(2000)
self._save_timer.timeout.connect(self._save_notes)

# On every keystroke:
def _on_notes_changed(self):
    self._save_timer.start()  # Resets the 2s countdown
```

### File Chips (`_FileChip`)

Compact `QFrame` showing: filename + size + × remove button. Uses `_FlowLayout` (custom `QLayout`) to wrap horizontally like text.

```python
class _FileChip(QtWidgets.QFrame):
    removeClicked = QtCore.Signal(Path)
    # Shows: [filename.pdf  2.1 MB  ×]
```

### File Upload

`_add_document()` opens a `QFileDialog`, copies selected files to `reference_docs/`, handles name collisions by appending `_1`, `_2`, etc.

Supported filter: `*.pdf *.png *.jpg *.jpeg *.svg *.dxf *.dwg`

## Backend Integration

### System Prompt Injection (`backends/claude_code.py`)

After building the base system prompt from the template, project context is appended:

```python
# Project notes (engineer-provided context)
if self.project_dir:
    project_md = Path(self.project_dir) / "project.md"
    if project_md.exists():
        notes = project_md.read_text(encoding="utf-8").strip()
        if notes:
            system_prompt += f"\n\n## Project Notes (from engineer)\n{notes}"

    # Reference docs listing
    ref_dir = Path(self.project_dir) / "reference_docs"
    if ref_dir.exists():
        docs = sorted(f for f in ref_dir.iterdir()
                       if f.is_file() and not f.name.startswith('.'))
        if docs:
            listing = "\n".join(
                f"- {f.name} ({f.stat().st_size / 1024:.0f} KB)"
                for f in docs
            )
            system_prompt += f"\n\n## Available Reference Documents\n{listing}"
            system_prompt += "\nUse the Read tool to consult these when relevant "
                             "(in reference_docs/ directory). For PDFs, use the pages parameter."
```

### Inner Claude's CLAUDE.md (`project_claude_template.md`)

The per-project CLAUDE.md template tells inner Claude about both sources:

```markdown
## Project Context
- `project.md` contains engineer-provided project notes (naming, materials, rules). Follow these.
- `reference_docs/` may contain project PDFs. Use Read tool to consult when relevant.
```

### How Inner Claude Uses Reference Docs

Reference documents are **listed** in the system prompt (name + size), not embedded. Inner Claude uses the `Read` tool on-demand to consult them:

```
System prompt: "Available Reference Documents:
  - structural_calcs.pdf (2100 KB)
  - soil_report.pdf (800 KB)
  Use the Read tool to consult these when relevant."

User: "Draw the pad footing from the calc sheet"

Claude: [Read tool] reference_docs/structural_calcs.pdf pages=1-5
         → Reads PDF content, extracts footing dimensions
         → Generates drawing code using the extracted values
```

This avoids embedding large PDFs in every request — Claude only reads what it needs.

## Files

| File | Role |
|------|------|
| `widgets/project_context.py` | Full-panel context editor widget |
| `DrawingPanel.py` | Header toggle button, QStackedWidget, project dir wiring |
| `backends/claude_code.py` | Reads project.md + lists reference_docs in system prompt |
| `project_claude_template.md` | Tells inner Claude about project.md and reference_docs/ |
