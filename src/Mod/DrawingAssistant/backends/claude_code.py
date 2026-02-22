# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Claude Code Backend - Uses Claude Code CLI in headless mode for LLM communication.

This backend replaces the HTTP API with subprocess calls to the Claude Code CLI,
giving access to richer context through file reading and project-specific CLAUDE.md.

Official documentation: https://code.claude.com/docs/en/headless
"""

import json
import os
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict
import FreeCAD


def _get_claude_command() -> list:
    """Get the command to invoke Claude Code CLI.

    On Windows, .cmd/.bat files require cmd.exe to execute, and cmd.exe
    ALWAYS creates a visible console window — no combination of
    CREATE_NO_WINDOW or STARTUPINFO flags can reliably prevent it.
    The only reliable fix is to resolve node.exe + cli.js and invoke
    them directly, completely bypassing cmd.exe.

    Uses 4 independent lookup strategies to find node.exe and cli.js,
    ensuring it works regardless of how Node.js/Claude were installed
    or whether Buildable was launched from a terminal or desktop shortcut.

    Returns:
        A list of command parts (e.g. ["node.exe", "cli.js"] or ["claude"]).
    """
    if sys.platform != "win32":
        return ["claude"]

    # --- Step 1: Find cli.js ---
    cli_js = None

    # 1a. Resolve via claude.cmd / claude in PATH
    for name in ("claude.cmd", "claude"):
        found = shutil.which(name)
        if found:
            candidate = Path(found).parent / "node_modules" / "@anthropic-ai" / "claude-code" / "cli.js"
            if candidate.exists():
                cli_js = candidate
                break

    # 1b. Try %APPDATA%\npm — npm's guaranteed global install directory on Windows
    if not cli_js:
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidate = Path(appdata) / "npm" / "node_modules" / "@anthropic-ai" / "claude-code" / "cli.js"
            if candidate.exists():
                cli_js = candidate

    # 1c. Try USERPROFILE fallback (covers edge case where APPDATA is unset)
    if not cli_js:
        userprofile = os.environ.get("USERPROFILE", "")
        if userprofile:
            candidate = Path(userprofile) / "AppData" / "Roaming" / "npm" / "node_modules" / "@anthropic-ai" / "claude-code" / "cli.js"
            if candidate.exists():
                cli_js = candidate

    if not cli_js:
        FreeCAD.Console.PrintWarning(
            "DrawingAssistant: Could not find claude-code cli.js — "
            "a CMD window may appear. Install with: npm install -g @anthropic-ai/claude-code\n"
        )
        return ["claude"]

    # --- Step 2: Find node.exe ---
    node_exe = None

    # 2a. Check the npm directory (some setups bundle node.exe there)
    npm_dir = cli_js.parents[3]  # cli.js -> claude-code -> @anthropic-ai -> node_modules -> npm_dir
    candidate = npm_dir / "node.exe"
    if candidate.exists():
        node_exe = str(candidate)

    # 2b. Try PATH
    if not node_exe:
        found = shutil.which("node.exe") or shutil.which("node")
        if found:
            node_exe = found

    # 2c. Try well-known Node.js install locations
    if not node_exe:
        for node_dir in [Path(r"C:\Program Files\nodejs"), Path(r"C:\Program Files (x86)\nodejs")]:
            candidate = node_dir / "node.exe"
            if candidate.exists():
                node_exe = str(candidate)
                break

    # 2d. Try Windows registry (Node.js installer registers its path here)
    if not node_exe:
        try:
            import winreg
            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(hive, r"SOFTWARE\Node.js") as key:
                        install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                        candidate = Path(install_path) / "node.exe"
                        if candidate.exists():
                            node_exe = str(candidate)
                            break
                except OSError:
                    pass
        except ImportError:
            pass

    if not node_exe:
        FreeCAD.Console.PrintWarning(
            "DrawingAssistant: Could not find node.exe — "
            "a CMD window may appear. Install Node.js from https://nodejs.org/\n"
        )
        return ["claude"]

    FreeCAD.Console.PrintMessage(
        f"DrawingAssistant: Resolved node={node_exe}, cli.js={cli_js}\n"
    )
    return [str(node_exe), str(cli_js)]


# System prompt template - general-purpose 2D drawing assistant
FREECAD_SYSTEM_PROMPT_TEMPLATE = """You are a FreeCAD 2D drawing assistant. You help users create and modify technical drawings using FreeCAD's Draft, TechDraw, and Spreadsheet workbenches.

Project directory: {pages_dir}

## How it works
Python scripts (*.py) in this directory define the drawing. Each file represents one drawing sheet. Underscore-prefixed files (_helpers.py) provide shared functions and run first; remaining files run alphabetically. You read and edit these scripts — FreeCAD renders the result.

The system clears and re-creates all objects when a file is re-executed. Do NOT use idempotent patterns (doc.getObject() or doc.addObject()) — just create objects directly.

## When the user asks a question
Respond with text only. Do NOT read or edit any files.

## When creating an execution plan (plan mode)
The user has enabled plan mode. You MUST NOT edit any files.
Read existing page files to understand the current drawing state, then create a step-by-step plan.

IMPORTANT: Write the plan for a STRUCTURAL ENGINEER, not a programmer. The user does not know Python, FreeCAD internals, or file names.
- Use engineering language: "draw a column cross-section", not "create Draft rectangles in pages/01_column_sections.py"
- Describe WHAT the drawing will show, not HOW it will be coded
- Include dimensions in mm, scales (e.g. 1:50), sheet sizes (A3 Landscape), and layout description
- Do NOT mention: file names, Python code, FreeCAD object types (DrawViewDraft, DocumentObjectGroup), function names, variable names, property names (FontSize, LineSpacing), or coordinate positions (X=200, Y=190)
- DO mention: what goes on the sheet, what scale, what dimensions, what annotations, what the final drawing will look like

Format each step as:
N. **Action**: Description in plain engineering terms

A good plan has 4-8 steps.

## When the user requests a drawing change
1. Read the sheet file to understand the current state
2. ALWAYS edit the existing file when modifying anything on that sheet (geometry, dimensions, annotations, layout, scale, views)
3. Only create a NEW file when the user asks for a NEW SHEET (e.g. "create a separate beam detail sheet")
4. Write code from your training knowledge, do NOT search the FreeCAD source first
5. Use descriptive Labels for objects so they're identifiable in the model tree

## File and sheet pattern
Each file = one complete drawing sheet. A file creates ALL geometry, groups, views, and layout for one sheet. This ensures views always reference groups created in the same file (no stale references across files).

Structure within a sheet file:
1. Constants and shared dimensions at the top
2. Drawing groups — each in its own section with a unique origin offset (>=15000mm apart):
   - Create geometry, collect in a `draft_objects_xxx` list
   - Create `App::DocumentObjectGroup`, set `grp.Group = draft_objects_xxx`
3. TechDraw page + template creation
4. ALL DrawViewDraft views with coordinated positions and scales
5. `doc.recompute()` at the end

Use `_helpers.py` for shared utility functions across sheets (e.g. hatching helpers, common dimension patterns). NEVER put TechDraw page/view code in underscore-prefixed files — they run before sheet files and cannot reference geometry from them.

## Rules for code
- All dimensions in millimeters
- End each script with doc.recompute()
- Coordinate system: X=right, Y=up (2D plan view)
- Each drawing group within a file MUST use a unique origin offset in Draft space so groups don't overlap in the 3D view. E.g. plan at (0,0), section at (20000,0), detail at (40000,0). Offset by at least 15000mm.

## FreeCAD 2D API Reference

### Draft (2D geometry)
- `Draft.make_wire(points, closed=False)` — polyline from list of FreeCAD.Vector
- `Draft.make_circle(radius, placement)` — 2nd arg MUST be `FreeCAD.Placement`, NOT a Vector
- `Draft.make_rectangle(length, height)` — axis-aligned rectangle
- `Draft.make_text(string_list, point)` — text annotation
- `Draft.make_label(target_point, placement)` — leader with text
- `Draft.make_linear_dimension(p1, p2, dim_line)` — linear dimension (ViewObject has NO ArrowSize attribute)
- `Draft.make_hatch(face, pattern_file, scale)` — hatching with PAT files

### TechDraw (drawing sheets)
- Template path: `FreeCAD.getResourceDir() + "Mod/TechDraw/Templates/ISO/<template>.svg"`
- DEFAULT template: A3_Landscape_blank.svg (no title block). Always use this unless the user asks for a title block.
- Other templates: A4_Landscape_blank.svg, A3_Landscape_TD.svg (with title block), A4_Landscape_TD.svg (with title block)
- Create page: `page = doc.addObject("TechDraw::DrawPage", "PageName")`
- Set template: `tpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template"); tpl.Template = path; page.Template = tpl`
- Title block fields (A3/A4_Landscape_TD.svg): call `doc.recompute()` first, then `tpl.setEditFieldContent("FieldName", "value")`. Field names: FC-Title, Subtitle, AuthorName, SupervisorName, CreationDate, CheckDate, scale, Weight, drawing_number, SheetNumber, copyright
- Add Draft view: group Draft objects into `App::DocumentObjectGroup`, then use ONE `DrawViewDraft` per group. Do NOT create one DrawViewDraft per object (causes overlapping frames).
- Example with two views on one sheet (use direct variable refs, never doc.getObject lookups):
  ```
  # --- Group 1: Plan view ---
  plan_objects = []
  # ... create geometry ...
  plan_grp = doc.addObject("App::DocumentObjectGroup", "PlanGroup")
  plan_grp.Group = plan_objects

  # --- Group 2: Section at offset (20000, 0) ---
  section_objects = []
  # ... create geometry ...
  sec_grp = doc.addObject("App::DocumentObjectGroup", "SectionGroup")
  sec_grp.Group = section_objects

  # --- TechDraw sheet ---
  page = doc.addObject("TechDraw::DrawPage", "Sheet")
  tpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
  tpl.Template = FreeCAD.getResourceDir() + "Mod/TechDraw/Templates/ISO/A3_Landscape_blank.svg"
  page.Template = tpl
  doc.recompute()

  # --- Views (MUST set X/Y AFTER addView — addView resets position) ---
  plan_view = doc.addObject("TechDraw::DrawViewDraft", "PlanView")
  plan_view.Source = plan_grp    # direct ref — always fresh
  plan_view.Scale = 0.02         # 1:50
  page.addView(plan_view)
  plan_view.X = 130; plan_view.Y = 170
  plan_view.FontSize = 5.0; plan_view.LineSpacing = 3.5

  sec_view = doc.addObject("TechDraw::DrawViewDraft", "SectionView")
  sec_view.Source = sec_grp      # direct ref — always fresh
  sec_view.Scale = 0.02
  page.addView(sec_view)
  sec_view.X = 330; sec_view.Y = 170
  sec_view.FontSize = 5.0; sec_view.LineSpacing = 3.5
  ```
- Sheet sizes: A3 Landscape = 420x297mm, A4 Landscape = 297x210mm.
- Page coordinate system: origin (0,0) is at BOTTOM-LEFT, X increases RIGHT, Y increases UP. So Y=0 is the BOTTOM of the page and Y=297 is the TOP. Title block occupies ~45mm at bottom (low Y values). Safe area for views: X 20-400, Y 50-260.
- Scale to fit: BEFORE setting view.Scale, you MUST compute the total geometry extent and pick a scale that fits. Write a comment showing the math:
  ```
  # Geometry extent: W_mm x H_mm (including axis extensions, dimensions, labels)
  # At 1:N (Scale=1/N): W_mm/N x H_mm/N on sheet
  # A3 usable area: 380 x 250mm -> pick 1:N where both fit
  ```
  Standard scales: 1:20, 1:50, 1:100, 1:200, 1:500. Pick the largest that fits with margin.
- Text size: set `view.FontSize` on DrawViewDraft to control text size on the sheet. Draft object FontSizes are IGNORED in the rendered view. Use FontSize=5.0 for 1:100 plans, FontSize=8.0 for 1:20 details. Larger scale -> larger FontSize.
- Line spacing: ALWAYS set `view.LineSpacing = view.FontSize * 0.7` alongside FontSize. Default LineSpacing=1.0 causes multi-line text to overlap.

### Spreadsheet (tables, schedules)
- Create: `sheet = doc.addObject("Spreadsheet::Sheet", "SheetName")`
- Set cells: `sheet.set("A1", "Header")`
- Embed in TechDraw: `view = doc.addObject("TechDraw::DrawViewSpreadsheet", "TableView")`

## Important gotchas
- Object `.Name` is read-only after creation — set only via `doc.addObject("Type", "DesiredName")`
- Use `.Label` for human-readable identification (can be changed anytime)
- Draft objects auto-generate Names — collect refs as you create them, don't filter by Name prefix later
- Delete document objects in REVERSE order (`reversed(doc.Objects)`) to avoid crashes from dangling links"""


class ClaudeCodeBackend:
    """LLM backend using Claude Code CLI in headless mode.

    Benefits over HTTP API:
    - Claude can read FreeCAD source code (.pyi stubs, docstrings)
    - Claude can read project files on-demand (pages/*.py, snapshots/)
    - Project-specific CLAUDE.md for custom instructions
    - Session continuity via --resume
    - Tool access (Glob, Grep, Read) for intelligent context gathering
    """

    def __init__(self, project_dir: str = None):
        """Initialize the Claude Code backend.

        Args:
            project_dir: Project directory for accessing pages/ and snapshots.
                        Note: Claude runs from repo root to access FreeCAD API docs.
        """
        self.project_dir = project_dir
        self._repo_root = self._find_repo_root()
        self._session_id: Optional[str] = None

        # Model identifier (matches LLMBackend interface)
        self.model = "claude-code"
        self.api_url = "claude-code-cli"  # Matches LLMBackend interface

        # Debug info (matches LLMBackend interface)
        self.last_duration_ms = 0
        self.last_cost = 0.0
        self.last_system_prompt = ""
        self.last_context = ""
        self.last_conversation = []
        self.last_tool_calls: List[Dict] = []  # Tool calls made during last request

        # Track which page files were edited (for direct source editing flow)
        self.edited_files: List[str] = []

        # Callback for real-time tool call updates (for progress indicator)
        # Signature: on_tool_call(tool_name: str, tool_input: dict)
        self.on_tool_call = None

        # Active subprocess handle (for cancellation via SIGINT)
        self._process: Optional[subprocess.Popen] = None
        self._cancelled = False  # Set by cancel(), checked after process exits

    def chat(
        self,
        user_message: str,
        context: str = "",
        history: list = None,
        multi_angle_screenshots: list = None,
        read_only: bool = False,
    ) -> str:
        """Send message to Claude Code CLI and get response.

        Args:
            user_message: The user's natural language request
            context: Optional document context string (passed in prompt if no CLAUDE.md)
            history: Optional conversation history (not used - Claude Code manages sessions)
            multi_angle_screenshots: Optional list of file paths to multi-angle screenshots
            read_only: If True, restrict to Read/Glob/Grep tools only (for plan mode)

        Returns:
            Generated response (Python code or text answer)
        """
        # Store for debugging
        self.last_context = context
        self.last_conversation = history[-6:] if history else []

        # Build the prompt
        prompt = self._build_prompt(user_message, context, multi_angle_screenshots)

        # Build command - use stream-json for tool visibility
        # Note: stream-json requires --verbose when used with -p (print mode)
        claude_cmd = _get_claude_command()
        cmd = claude_cmd + ["-p", "--verbose", "--output-format", "stream-json"]

        # Tool access: --tools restricts which tools exist in context,
        # --allowedTools auto-approves tools without prompting.
        # Phase 1 (read_only): --tools removes Edit/Write/ExitPlanMode entirely
        # Phase 2 / normal: --allowedTools auto-approves all needed tools
        if read_only:
            cmd.extend(["--tools", "Read,Glob,Grep"])
        else:
            cmd.extend(["--allowedTools", "Read,Glob,Grep,Edit,Write"])

        # Build system prompt
        pages_dir = self._get_pages_dir()

        system_prompt = FREECAD_SYSTEM_PROMPT_TEMPLATE.format(
            pages_dir=pages_dir or "(no project)",
        )

        # Append engineer's project notes (from project.md)
        if self.project_dir:
            project_md = Path(self.project_dir) / "project.md"
            if project_md.exists():
                try:
                    notes = project_md.read_text(encoding="utf-8").strip()
                    if notes:
                        system_prompt += (
                            f"\n\n## Project Notes (from engineer)\n{notes}"
                        )
                except Exception as e:
                    FreeCAD.Console.PrintWarning(
                        f"DrawingAssistant: Failed to read project.md: {e}\n"
                    )

            # Append reference documents listing
            ref_dir = Path(self.project_dir) / "reference_docs"
            if ref_dir.exists():
                docs = sorted(
                    f for f in ref_dir.iterdir()
                    if f.is_file() and not f.name.startswith(".")
                )
                if docs:
                    listing = "\n".join(
                        f"- {f.name} ({f.stat().st_size / 1024:.0f} KB)"
                        for f in docs
                    )
                    system_prompt += (
                        f"\n\n## Available Reference Documents\n{listing}\n"
                        "Use the Read tool to consult these when relevant "
                        "(in reference_docs/ directory). "
                        "For PDFs, use the pages parameter."
                    )

        cmd.extend(["--append-system-prompt", system_prompt])
        self.last_system_prompt = system_prompt

        # Resume session if we have one (for multi-turn conversations)
        if self._session_id:
            cmd.extend(["--resume", self._session_id])

        # NOTE: Prompt is passed via stdin, not as command line argument
        # This avoids shell escaping issues with special characters

        # Set working directory to PROJECT directory (so Claude can edit pages/)
        # Claude can still read API docs via absolute paths in the prompt
        cwd = self.project_dir or self._repo_root or os.getcwd()

        FreeCAD.Console.PrintMessage(f"DrawingAssistant: Calling Claude Code in {cwd}\n")

        # Reset state for this request
        self.last_tool_calls = []
        self.edited_files = []
        self._cancelled = False

        start_time = time.time()
        try:
            # Use Popen for streaming NDJSON output
            # Hide console window on Windows
            kwargs = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = 0  # SW_HIDE
                kwargs["startupinfo"] = si

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",  # Explicit UTF-8 for Windows compatibility
                cwd=cwd,
                **kwargs
            )
            self._process = process

            # Write prompt to stdin and close
            process.stdin.write(prompt)
            process.stdin.close()

            # Parse NDJSON stream line by line
            result_text = ""
            assistant_text_parts = []  # Fallback: accumulate text from assistant events
            tool_calls = []

            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type")

                # Extract text and tool_use from assistant messages
                if event_type == "assistant":
                    message = event.get("message", {})
                    for block in message.get("content", []):
                        if block.get("type") == "text":
                            assistant_text_parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            tool_input = block.get("input", {})
                            tool_call = {
                                "tool": tool_name,
                                "input": tool_input
                            }
                            tool_calls.append(tool_call)
                            # Log with details
                            detail = self._format_tool_log(tool_name, tool_input)
                            FreeCAD.Console.PrintMessage(
                                f"DrawingAssistant: Tool call - {detail}\n"
                            )
                            # Fire callback for progress indicator
                            if self.on_tool_call:
                                self.on_tool_call(tool_name, tool_input)

                # Handle final result
                elif event_type == "result":
                    result_text = event.get("result", "")
                    self._session_id = event.get("session_id")

                    # Debug: log result content
                    FreeCAD.Console.PrintMessage(
                        f"DrawingAssistant: Result event - length: {len(result_text)}, "
                        f"preview: {result_text[:100] if result_text else '(empty)'}...\n"
                    )

                    # Track cost
                    self.last_cost = event.get("total_cost_usd", 0)

                    # Check for error
                    if event.get("is_error", False):
                        error_msg = result_text or "Unknown error"
                        FreeCAD.Console.PrintError(
                            f"DrawingAssistant: Claude Code returned error: {error_msg}\n"
                        )
                        self.last_duration_ms = (time.time() - start_time) * 1000
                        return f"# Error: {error_msg}"

            # Wait for process to complete
            # Use shorter timeout if cancelled (SIGINT should exit quickly)
            wait_timeout = 10 if self._cancelled else 180
            try:
                process.wait(timeout=wait_timeout)
            except subprocess.TimeoutExpired:
                # Process didn't exit in time — force kill
                FreeCAD.Console.PrintWarning(
                    "DrawingAssistant: Process didn't exit after "
                    f"{wait_timeout}s, killing\n"
                )
                process.kill()
                process.wait(timeout=5)

            self.last_duration_ms = (time.time() - start_time) * 1000

            # Store tool calls for UI access
            self.last_tool_calls = tool_calls

            # Check if we cancelled this request
            if self._cancelled:
                FreeCAD.Console.PrintMessage(
                    "DrawingAssistant: Claude Code request was cancelled\n"
                )
                return None  # Sentinel: cancelled, not an error

            # Track which page files were edited (for direct source editing flow)
            self.edited_files = []
            for tc in tool_calls:
                tool_name = tc.get("tool")
                if tool_name in ("Edit", "Write"):
                    file_path = tc.get("input", {}).get("file_path", "")
                    if "/pages/" in file_path and file_path.endswith(".py"):
                        filename = Path(file_path).name
                        if filename not in self.edited_files:
                            self.edited_files.append(filename)
                            FreeCAD.Console.PrintMessage(
                                f"DrawingAssistant: Detected page {tool_name.lower()}: {filename}\n"
                            )

            # Check for process errors
            if process.returncode != 0:
                stderr = process.stderr.read()
                FreeCAD.Console.PrintError(f"DrawingAssistant: Claude Code error: {stderr}\n")
                return f"# Error: {stderr}"

            # Fallback: if result is empty, use accumulated assistant text
            if not result_text and assistant_text_parts:
                result_text = "\n".join(assistant_text_parts)
                FreeCAD.Console.PrintMessage(
                    "DrawingAssistant: Result was empty, using assistant text fallback\n"
                )

            FreeCAD.Console.PrintMessage(
                f"DrawingAssistant: Claude Code response received "
                f"({self.last_duration_ms:.0f}ms, ${self.last_cost:.4f}, "
                f"{len(tool_calls)} tool calls)\n"
            )

            return self._clean_response(result_text)

        except json.JSONDecodeError as e:
            FreeCAD.Console.PrintError(f"DrawingAssistant: Failed to parse Claude Code response: {e}\n")
            return f"# Error: Failed to parse response: {e}"

        except FileNotFoundError:
            FreeCAD.Console.PrintError("DrawingAssistant: Claude Code CLI not found. Is it installed?\n")
            return "# Error: Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"

        except Exception as e:
            FreeCAD.Console.PrintError(f"DrawingAssistant: Claude Code error: {e}\n")
            return f"# Error: {e}"

        finally:
            self._process = None

    def cancel(self):
        """Send SIGINT to the running Claude Code process for graceful interruption.

        Claude Code saves session state on SIGINT, so --resume will continue
        the conversation including the interrupted turn.
        """
        self._cancelled = True
        if self._process and self._process.poll() is None:
            FreeCAD.Console.PrintMessage("DrawingAssistant: Sending SIGINT to Claude Code process\n")
            if sys.platform == "win32":
                self._process.terminate()
            else:
                self._process.send_signal(signal.SIGINT)

    def _build_prompt(self, message: str, context: str,
                       multi_angle_screenshots: list = None) -> str:
        """Build the prompt for Claude Code.

        User message comes FIRST for prominence.
        Pages directory path is in the system prompt — not repeated here to avoid
        tempting Claude to read files for pure questions.
        """
        parts = []

        # User message FIRST — don't bury it under context
        parts.append(message)
        parts.append("")

        # Always include document context
        if context:
            parts.append(f"## Document State\n{context}")
            parts.append("")

        # Screenshots (user-attached + auto-generated)
        if multi_angle_screenshots:
            user_images = [p for p in multi_angle_screenshots if "/user_uploads/" in p]
            auto_images = [p for p in multi_angle_screenshots if "/user_uploads/" not in p]

            if user_images:
                parts.append("### User-attached images:")
                for path in user_images:
                    parts.append(f"- {path}")
                parts.append("")

            if auto_images:
                parts.append("### Current state:")
                for path in auto_images:
                    filename = Path(path).name
                    if "review_top" in filename:
                        parts.append(f"- Top view (Draft geometry): {path}")
                    else:
                        parts.append(f"- {filename}: {path}")
                parts.append("")

        return "\n".join(parts)

    def _clean_response(self, response: str) -> str:
        """Clean up the response - remove markdown code blocks if present."""
        response = response.strip()

        # Remove markdown code fences
        if response.startswith("```python"):
            response = response[9:]
        elif response.startswith("```"):
            response = response[3:]

        if response.endswith("```"):
            response = response[:-3]

        return response.strip()

    def _format_tool_log(self, tool: str, input_data: dict) -> str:
        """Format tool call for console logging with details."""
        if tool == "Glob":
            pattern = input_data.get("pattern", "")
            return f"Glob: {pattern}"
        elif tool == "Read":
            path = input_data.get("file_path", "")
            if len(path) > 60:
                path = "..." + path[-57:]
            return f"Read: {path}"
        elif tool == "Grep":
            pattern = input_data.get("pattern", "")
            path = input_data.get("path", ".")
            if len(path) > 30:
                path = "..." + path[-27:]
            return f"Grep: '{pattern}' in {path}"
        elif tool == "Edit":
            path = input_data.get("file_path", "")
            if len(path) > 50:
                path = "..." + path[-47:]
            return f"Edit: {path}"
        elif tool == "Write":
            path = input_data.get("file_path", "")
            if len(path) > 50:
                path = "..." + path[-47:]
            return f"Write: {path}"
        elif tool == "Bash":
            cmd = input_data.get("command", "")
            if len(cmd) > 50:
                cmd = cmd[:47] + "..."
            return f"Bash: {cmd}"
        elif tool == "Task":
            desc = input_data.get("description", "")
            return f"Task: {desc}"
        else:
            return f"{tool}"

    def _get_pages_dir(self) -> Optional[str]:
        """Get absolute path to pages/ directory for the project."""
        if self.project_dir:
            pages_dir = Path(self.project_dir) / "pages"
            return str(pages_dir.resolve())
        return None

    @property
    def source_was_edited(self) -> bool:
        """Backward compat: True if any page file was edited."""
        return len(self.edited_files) > 0

    def _find_repo_root(self) -> Optional[str]:
        """Find FreeCAD repo root directory.

        Walks up from this file's location to find the directory containing src/Mod/.
        This allows Claude to read FreeCAD API source files (.pyi stubs, docstrings).

        Returns:
            Repo root path, or None if not found
        """
        current = Path(__file__).resolve().parent
        # Walk up to find repo root (contains src/Mod/)
        while current.parent != current:
            if (current / "src" / "Mod").exists():
                return str(current)
            current = current.parent
        return None

    def clear_session(self):
        """Clear the current session (start fresh conversation)."""
        self._session_id = None
        FreeCAD.Console.PrintMessage("DrawingAssistant: Claude Code session cleared\n")

    def get_session_id(self) -> Optional[str]:
        """Get the current session ID for persistence."""
        return self._session_id

    def set_session_id(self, session_id: str):
        """Restore a session ID (for resuming conversations)."""
        self._session_id = session_id
