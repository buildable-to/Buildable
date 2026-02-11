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
            "AIAssistant: Could not find claude-code cli.js — "
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
            "AIAssistant: Could not find node.exe — "
            "a CMD window may appear. Install Node.js from https://nodejs.org/\n"
        )
        return ["claude"]

    FreeCAD.Console.PrintMessage(
        f"AIAssistant: Resolved node={node_exe}, cli.js={cli_js}\n"
    )
    return [str(node_exe), str(cli_js)]


# System prompt template - minimal framing, no API examples
FREECAD_SYSTEM_PROMPT_TEMPLATE = """You are a FreeCAD AI assistant that helps with 3D designs.

source.py: {source_path}
FreeCAD source: {repo_root}

## When the user asks a question
Respond with text only. Do NOT read or edit any files.

## When the user requests a design change
1. Read source.py to understand the current design
2. Edit source.py to make the change — write code from your training knowledge, do NOT search the FreeCAD source first

## Rules for code
- All dimensions in millimeters
- End with doc.recompute()
- Use descriptive Labels, reference objects by Name in code
- Coordinate system: X=right, Y=forward, Z=up (right-handed)
- XY_Plane=horizontal, XZ_Plane=vertical south-facing, YZ_Plane=vertical west-facing"""


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

        # Callback for real-time tool call updates (for progress indicator)
        # Signature: on_tool_call(tool_name: str, tool_input: dict)
        self.on_tool_call = None

    def chat(
        self,
        user_message: str,
        context: str = "",
        history: list = None,
        screenshot: str = None,
        multi_angle_screenshots: list = None,
    ) -> str:
        """Send message to Claude Code CLI and get response.

        Args:
            user_message: The user's natural language request
            context: Optional document context string (passed in prompt if no CLAUDE.md)
            history: Optional conversation history (not used - Claude Code manages sessions)
            screenshot: Optional base64-encoded PNG screenshot (saved to temp file)
            multi_angle_screenshots: Optional list of file paths to multi-angle screenshots

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
        prompt = self._build_prompt(user_message, context, screenshot_path, multi_angle_screenshots)

        # Build command - use stream-json for tool visibility
        # Note: stream-json requires --verbose when used with -p (print mode)
        claude_cmd = _get_claude_command()
        cmd = claude_cmd + ["-p", "--verbose", "--output-format", "stream-json"]

        # Allow Edit and Write tools for direct source.py modification
        cmd.extend(["--allowedTools", "Read,Glob,Grep,Edit,Write"])

        # Build system prompt
        source_path = self._get_source_path()
        repo_root = self._repo_root or ""

        system_prompt = FREECAD_SYSTEM_PROMPT_TEMPLATE.format(
            source_path=source_path or "(no project)",
            repo_root=repo_root,
        )
        cmd.extend(["--append-system-prompt", system_prompt])
        self.last_system_prompt = system_prompt

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
                            # Fire callback for progress indicator
                            if self.on_tool_call:
                                self.on_tool_call(tool_name, tool_input)

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

    def _build_prompt(self, message: str, context: str, screenshot_path: str = None,
                       multi_angle_screenshots: list = None) -> str:
        """Build the prompt for Claude Code.

        User message comes FIRST for prominence.
        source.py path is in the system prompt — not repeated here to avoid
        tempting Claude to read it for pure questions.
        """
        parts = []

        # User message FIRST — don't bury it under context
        parts.append(message)
        parts.append("")

        # Always include document context
        if context:
            parts.append(f"## Document State\n{context}")
            parts.append("")

        # Screenshots
        if screenshot_path:
            parts.append(f"[Screenshot of current viewport: {screenshot_path}]")

        if multi_angle_screenshots:
            parts.append("### Multi-angle screenshots:")
            for path in multi_angle_screenshots:
                filename = Path(path).name
                view_name = filename.rsplit("_", 1)[-1].replace(".png", "") if "_" in filename else "view"
                parts.append(f"- {view_name}: {path}")
            parts.append("")

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
        FreeCAD.Console.PrintMessage("AIAssistant: Claude Code session cleared\n")

    def get_session_id(self) -> Optional[str]:
        """Get the current session ID for persistence."""
        return self._session_id

    def set_session_id(self, session_id: str):
        """Restore a session ID (for resuming conversations)."""
        self._session_id = session_id
