"""Standalone Claude Code CLI wrapper for web PoC — zero FreeCAD deps."""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


# System prompt for the inner Claude — teaches it to work with source.py
SYSTEM_PROMPT = """You are a FreeCAD 3D modeling assistant. You help users create and modify 3D models by editing source.py.

source.py location: {source_path}

## When the user asks a question
Respond with text only. Do NOT read or edit any files.

## When the user requests a design change
1. Read source.py to understand the current design
2. Edit source.py to make the change

## Rules for code in source.py
- Use `import FreeCAD`, `import Part`
- Create document: `doc = FreeCAD.newDocument("Design")`
- Primitives: `Part.makeBox(l,w,h)`, `Part.makeCylinder(r,h)`, `Part.makeSphere(r)`, `Part.makeCone(r1,r2,h)`, `Part.makeTorus(r1,r2)`
- Placement: `FreeCAD.Vector(x,y,z)`, `FreeCAD.Placement(Vector, Rotation)`
- Booleans: `shape.fuse(other)`, `shape.cut(other)`, `shape.common(other)`
- Show result: `Part.show(shape, "Name")`
- Always end with `doc.recompute()`
- All dimensions in millimeters
- Coordinate system: X=right, Y=forward, Z=up
- Keep the script self-contained — it must run from scratch each time
- Use descriptive names for Part.show() calls"""


def _find_claude_cmd() -> list:
    """Find the claude CLI binary."""
    if sys.platform != "win32":
        return ["claude"]
    # On Windows, try to find node + cli.js to avoid CMD window
    found = shutil.which("claude.cmd") or shutil.which("claude")
    if found:
        cli_js = Path(found).parent / "node_modules" / "@anthropic-ai" / "claude-code" / "cli.js"
        if cli_js.exists():
            node = shutil.which("node.exe") or shutil.which("node")
            if node:
                return [node, str(cli_js)]
    return ["claude"]


class ClaudeChat:
    """Lightweight Claude Code CLI wrapper for web chat."""

    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.session_id: Optional[str] = None
        self.source_was_edited: bool = False

    def get_source_path(self) -> str:
        return str(Path(self.project_dir) / "source.py")

    def chat(self, message: str) -> dict:
        """Send a message to Claude and get a response.

        Returns:
            {response: str, session_id: str, source_edited: bool}
        """
        self.source_was_edited = False

        # Build command
        cmd = _find_claude_cmd() + [
            "-p", "--verbose",
            "--output-format", "stream-json",
            "--allowedTools", "Edit,Write,Read",
        ]

        # System prompt
        system_prompt = SYSTEM_PROMPT.format(source_path=self.get_source_path())
        cmd.extend(["--append-system-prompt", system_prompt])

        # Resume session for multi-turn
        if self.session_id:
            cmd.extend(["--resume", self.session_id])

        # Spawn process
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            cwd=self.project_dir,
            **kwargs,
        )

        # Send prompt via stdin
        process.stdin.write(message)
        process.stdin.close()

        # Parse NDJSON stream
        result_text = ""
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = event.get("type")

            if event_type == "assistant":
                # Track tool calls for Edit/Write on source.py
                for block in event.get("message", {}).get("content", []):
                    if block.get("type") == "tool_use":
                        tool = block.get("name", "")
                        if tool in ("Edit", "Write"):
                            file_path = block.get("input", {}).get("file_path", "")
                            if "source.py" in file_path:
                                self.source_was_edited = True

            elif event_type == "result":
                result_text = event.get("result", "")
                self.session_id = event.get("session_id")
                if event.get("is_error"):
                    result_text = f"Error: {result_text}"

        process.wait(timeout=180)

        if process.returncode != 0 and not result_text:
            stderr = process.stderr.read()
            result_text = f"Error: {stderr}"

        return {
            "response": result_text.strip(),
            "session_id": self.session_id,
            "source_edited": self.source_was_edited,
        }
