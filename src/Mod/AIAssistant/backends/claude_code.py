# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Claude Code Backend - Uses Claude Code CLI in headless mode for LLM communication.

This backend replaces the HTTP API with subprocess calls to the Claude Code CLI,
giving access to richer context through file reading and project-specific CLAUDE.md.

Official documentation: https://code.claude.com/docs/en/headless
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict
import FreeCAD


def _get_claude_command() -> str:
    """Get the correct claude command for the current platform.

    On Windows with npm install, the command is 'claude.cmd'.
    On Linux/macOS or Windows native install, it's 'claude'.
    """
    if sys.platform == "win32":
        # Try to find claude in PATH
        claude_path = shutil.which("claude")
        if claude_path:
            return claude_path
        # Try claude.cmd (npm global install on Windows)
        claude_cmd = shutil.which("claude.cmd")
        if claude_cmd:
            return claude_cmd
        # Fallback - let subprocess handle it
        return "claude"
    else:
        return "claude"


# System prompt template - filled at runtime with workbench-specific info
FREECAD_SYSTEM_PROMPT_TEMPLATE = """You are a FreeCAD AI assistant.
Edit source.py directly to make design changes.

source.py location: {source_path}
Current workbench: {workbench}
FreeCAD repo root: {repo_root}

WORKFLOW:
1. Read source.py to understand current design
2. Use Edit tool to modify source.py directly
3. CREATE objects: Add code to source.py
4. DELETE objects: Remove the relevant code from source.py
5. MODIFY objects: Edit the relevant code in source.py

## IMPORTANT: Use the correct API for the current workbench

**You MUST use APIs appropriate for "{workbench}".**

{api_reference}

## How to Learn the API
If you need to understand a FreeCAD API function, read the actual source files:
- Use Glob to find relevant files: `src/Mod/<Workbench>/`
- Use Read to examine function signatures and docstrings
- The source code is the authoritative reference

## Code Rules
- Use millimeters for all dimensions
- End code with doc.recompute()
- Use descriptive Labels for objects
- Use object Names (not Labels) when referencing in code

To ANSWER questions (not modify design): Return clear text explanation."""


# Workbench API references - point to actual source files
WORKBENCH_API_REFS = {
    "Draft": """For 2D drafting, use the Draft module:
- API source: {repo_root}/src/Mod/Draft/draftmake/ (make_line.py, make_circle.py, etc.)
- Import: `import Draft`
- Key functions: Draft.make_line(), Draft.make_wire(), Draft.make_circle(), Draft.make_rectangle(), Draft.make_polygon(), Draft.make_text()
- All Z coordinates should be 0 for 2D drawings""",

    "Part": """For 3D solid modeling, use the Part module:
- API source: {repo_root}/src/Mod/Part/App/
- Import: `import Part`
- Key functions: Part.makeBox(), Part.makeCylinder(), Part.makeSphere(), shape.fuse(), shape.cut()
- Reference: {repo_root}/src/Mod/AIAssistant/FREECAD_API.md""",

    "PartDesign": """For parametric feature-based modeling, use PartDesign:
- API source: {repo_root}/src/Mod/PartDesign/
- Work inside a Body: doc.addObject("PartDesign::Body", "Body")
- Create sketches, then Pad/Pocket/Revolve them""",

    "Sketcher": """For constraint-based 2D sketching:
- API source: {repo_root}/src/Mod/Sketcher/
- Import: `import Sketcher`
- Create fully constrained sketches for PartDesign""",

    "BIM": """For architectural elements:
- API source: {repo_root}/src/Mod/BIM/
- Import: `import Arch`
- Key functions: Arch.makeWall(), Arch.makeStructure(), Arch.makeWindow()""",

    "Arch": """For architectural elements:
- API source: {repo_root}/src/Mod/Arch/
- Import: `import Arch`
- Key functions: Arch.makeWall(), Arch.makeStructure(), Arch.makeWindow()""",

    "TechDraw": """For technical drawings:
- API source: {repo_root}/src/Mod/TechDraw/
- Create pages and add views of 3D objects""",
}


class ClaudeCodeBackend:
    """LLM backend using Claude Code CLI in headless mode.

    Benefits over HTTP API:
    - Claude can read FreeCAD source code (.pyi stubs, docstrings)
    - Claude can read project files on-demand (source.py, snapshots/)
    - Project-specific CLAUDE.md for custom instructions
    - Session continuity via --resume
    - Tool access (Glob, Grep, Read) for intelligent context gathering
    """

    def __init__(self, project_dir: str = None):
        """Initialize the Claude Code backend.

        Args:
            project_dir: Project directory for accessing source.py and snapshots.
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

        # Track if source.py was edited (for direct source editing flow)
        self.source_was_edited: bool = False

    def chat(
        self,
        user_message: str,
        context: str = "",
        history: list = None,
        screenshot: str = None,
    ) -> str:
        """Send message to Claude Code CLI and get response.

        Args:
            user_message: The user's natural language request
            context: Optional document context string (passed in prompt if no CLAUDE.md)
            history: Optional conversation history (not used - Claude Code manages sessions)
            screenshot: Optional base64-encoded PNG screenshot (saved to temp file)

        Returns:
            Generated response (Python code or text answer)
        """
        # Store for debugging
        self.last_context = context
        self.last_conversation = history[-6:] if history else []

        # Handle screenshot - save to temp file for Claude to read
        screenshot_path = None
        if screenshot:
            screenshot_path = self._save_screenshot(screenshot)

        # Build the prompt
        prompt = self._build_prompt(user_message, context, screenshot_path)

        # Build command - use stream-json for tool visibility
        # Note: stream-json requires --verbose when used with -p (print mode)
        claude_cmd = _get_claude_command()
        cmd = [claude_cmd, "-p", "--verbose", "--output-format", "stream-json"]

        # Allow Edit and Write tools for direct source.py modification
        cmd.extend(["--allowedTools", "Read,Glob,Grep,Edit,Write"])

        # Build system prompt with workbench-specific info
        # ALWAYS include workbench context, even if project has CLAUDE.md
        source_path = self._get_source_path()
        workbench = self._get_active_workbench()
        repo_root = self._repo_root or ""

        # Get workbench-specific API reference
        api_ref = WORKBENCH_API_REFS.get(workbench, "")
        if api_ref:
            api_ref = api_ref.format(repo_root=repo_root)

        system_prompt = FREECAD_SYSTEM_PROMPT_TEMPLATE.format(
            source_path=source_path or "(no project)",
            workbench=workbench,
            repo_root=repo_root,
            api_reference=api_ref
        )
        cmd.extend(["--append-system-prompt", system_prompt])
        self.last_system_prompt = system_prompt

        FreeCAD.Console.PrintMessage(f"AIAssistant: Using workbench: {workbench}\n")

        # Resume session if we have one (for multi-turn conversations)
        if self._session_id:
            cmd.extend(["--resume", self._session_id])

        # NOTE: Prompt is passed via stdin, not as command line argument
        # This avoids shell escaping issues with special characters

        # Set working directory to PROJECT directory (so Claude can edit source.py)
        # Claude can still read API docs via absolute paths in the prompt
        cwd = self.project_dir or self._repo_root or os.getcwd()

        FreeCAD.Console.PrintMessage(f"AIAssistant: Calling Claude Code in {cwd}\n")

        # Reset state for this request
        self.last_tool_calls = []
        self.source_was_edited = False

        start_time = time.time()
        try:
            # Use Popen for streaming NDJSON output
            # Hide console window on Windows
            kwargs = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

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

            # Write prompt to stdin and close
            process.stdin.write(prompt)
            process.stdin.close()

            # Parse NDJSON stream line by line
            result_text = ""
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

                # Extract tool_use from assistant messages
                if event_type == "assistant":
                    message = event.get("message", {})
                    for block in message.get("content", []):
                        if block.get("type") == "tool_use":
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
                                f"AIAssistant: Tool call - {detail}\n"
                            )

                # Handle final result
                elif event_type == "result":
                    result_text = event.get("result", "")
                    self._session_id = event.get("session_id")

                    # Debug: log result content
                    FreeCAD.Console.PrintMessage(
                        f"AIAssistant: Result event - length: {len(result_text)}, "
                        f"preview: {result_text[:100] if result_text else '(empty)'}...\n"
                    )

                    # Track cost
                    self.last_cost = event.get("total_cost_usd", 0)

                    # Check for error
                    if event.get("is_error", False):
                        error_msg = result_text or "Unknown error"
                        FreeCAD.Console.PrintError(
                            f"AIAssistant: Claude Code returned error: {error_msg}\n"
                        )
                        self.last_duration_ms = (time.time() - start_time) * 1000
                        return f"# Error: {error_msg}"

            # Wait for process to complete
            process.wait(timeout=180)
            self.last_duration_ms = (time.time() - start_time) * 1000

            # Store tool calls for UI access
            self.last_tool_calls = tool_calls

            # Track if source.py was edited (for direct source editing flow)
            for tc in tool_calls:
                tool_name = tc.get("tool")
                if tool_name in ("Edit", "Write"):
                    file_path = tc.get("input", {}).get("file_path", "")
                    if "source.py" in file_path:
                        self.source_was_edited = True
                        FreeCAD.Console.PrintMessage(
                            f"AIAssistant: Detected source.py {tool_name.lower()}\n"
                        )
                        break

            # Check for process errors
            if process.returncode != 0:
                stderr = process.stderr.read()
                FreeCAD.Console.PrintError(f"AIAssistant: Claude Code error: {stderr}\n")
                return f"# Error: {stderr}"

            FreeCAD.Console.PrintMessage(
                f"AIAssistant: Claude Code response received "
                f"({self.last_duration_ms:.0f}ms, ${self.last_cost:.4f}, "
                f"{len(tool_calls)} tool calls)\n"
            )

            return self._clean_response(result_text)

        except subprocess.TimeoutExpired:
            self.last_duration_ms = (time.time() - start_time) * 1000
            FreeCAD.Console.PrintError("AIAssistant: Claude Code request timed out\n")
            return "# Error: Request timed out"

        except json.JSONDecodeError as e:
            FreeCAD.Console.PrintError(f"AIAssistant: Failed to parse Claude Code response: {e}\n")
            return f"# Error: Failed to parse response: {e}"

        except FileNotFoundError:
            FreeCAD.Console.PrintError("AIAssistant: Claude Code CLI not found. Is it installed?\n")
            return "# Error: Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"

        except Exception as e:
            FreeCAD.Console.PrintError(f"AIAssistant: Claude Code error: {e}\n")
            return f"# Error: {e}"

    def _build_prompt(self, message: str, context: str, screenshot_path: str = None) -> str:
        """Build the prompt for Claude Code.

        Claude runs from project directory and can edit source.py directly.
        FreeCAD API docs are accessible via absolute paths in the system prompt.
        """
        parts = []

        # Include project info in prompt
        if self.project_dir:
            project_path = Path(self.project_dir).resolve()
            parts.append(f"Project directory: {project_path}")
            source_file = project_path / "source.py"
            if source_file.exists():
                parts.append(f"Code history: {source_file}")
            parts.append("")  # Blank line

        # If no project CLAUDE.md exists, include context directly
        if self.project_dir:
            claude_md_path = Path(self.project_dir) / "CLAUDE.md"
            if not claude_md_path.exists() and context:
                parts.append(f"CURRENT DOCUMENT STATE:\n{context}\n")
        elif context:
            parts.append(f"CURRENT DOCUMENT STATE:\n{context}\n")

        # Add screenshot reference if provided
        if screenshot_path:
            parts.append(f"[Screenshot of current viewport: {screenshot_path}]\n")

        parts.append(message)

        return "\n".join(parts)

    def _save_screenshot(self, base64_data: str) -> str:
        """Save base64 screenshot to project directory for Claude to read.

        Screenshots are saved to {project_dir}/screenshots/ with timestamps.
        They are kept for debugging/logging purposes (not deleted after use).

        Args:
            base64_data: Base64-encoded PNG image

        Returns:
            Path to saved screenshot file
        """
        import base64
        from datetime import datetime

        if not self.project_dir:
            FreeCAD.Console.PrintWarning("AIAssistant: No project dir, cannot save screenshot\n")
            return None

        try:
            # Create screenshots directory
            screenshots_dir = Path(self.project_dir) / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)

            # Find next counter (like snapshots: 001, 002, etc.)
            existing = list(screenshots_dir.glob("*.png"))
            max_num = 0
            for f in existing:
                try:
                    num = int(f.stem.split("_")[0])
                    max_num = max(max_num, num)
                except (ValueError, IndexError):
                    pass
            next_num = max_num + 1

            # Generate filename: 001_2026-01-16_22-05.png
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = f"{next_num:03d}_{timestamp}.png"
            path = screenshots_dir / filename

            # Decode and save
            image_data = base64.b64decode(base64_data)
            path.write_bytes(image_data)

            FreeCAD.Console.PrintMessage(f"AIAssistant: Screenshot saved to {path}\n")
            return str(path)
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"AIAssistant: Failed to save screenshot: {e}\n")
            return None

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

    def _get_source_path(self) -> Optional[str]:
        """Get absolute path to source.py for the project."""
        if self.project_dir:
            source_path = Path(self.project_dir) / "source.py"
            return str(source_path.resolve())
        return None

    def _has_claude_md(self) -> bool:
        """Check if project has CLAUDE.md file.

        If CLAUDE.md exists in the project directory, Claude Code will
        automatically load it as context instructions.
        """
        if self.project_dir:
            return (Path(self.project_dir) / "CLAUDE.md").exists()
        return False

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

    def _get_active_workbench(self) -> str:
        """Get the name of the currently active workbench.

        Returns:
            Workbench name (e.g., "Draft", "Part", "PartDesign") or "Part" as default
        """
        try:
            import FreeCADGui
            wb = FreeCADGui.activeWorkbench()
            if wb:
                # Get workbench name and clean it up
                wb_name = wb.name() if hasattr(wb, 'name') else str(type(wb).__name__)
                # Remove "Workbench" suffix if present
                wb_name = wb_name.replace("Workbench", "").strip()
                return wb_name
        except Exception:
            pass
        return "Part"  # Default to Part workbench

    def clear_session(self):
        """Clear the current session (start fresh conversation)."""
        self._session_id = None
        FreeCAD.Console.PrintMessage("AIAssistant: Claude Code session cleared\n")

    def get_session_id(self) -> Optional[str]:
        """Get the current session ID for persistence."""
        return self._session_id

    def set_session_id(self, session_id: str):
        """Restore a session ID (for resuming conversations)."""
        self._session_id = session_id
