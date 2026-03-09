"""FreeCAD Web 3D Viewer — minimal PoC server with AI chat."""

import asyncio
import base64
import json
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse

from claude_chat import ClaudeChat

app = FastAPI()

FREECAD_CMD = Path(__file__).resolve().parent.parent / "build" / "debug" / "bin" / "FreeCADCmd"
INDEX_HTML = Path(__file__).resolve().parent / "index.html"

SEED_SOURCE = """\
import FreeCAD
import Part
doc = FreeCAD.newDocument("Design")
doc.recompute()
"""

EXPORT_TRAILER = """
# --- auto-injected STL export trailer ---
import Mesh, Part

shapes = []
for obj in FreeCAD.ActiveDocument.Objects:
    if hasattr(obj, "Shape") and not obj.Shape.isNull():
        shapes.append(obj.Shape)

if shapes:
    mesh = Mesh.Mesh()
    for s in shapes:
        mesh.addMesh(Mesh.Mesh(s.tessellate(0.1)))
    mesh.write("{stl_path}")
# No shapes → don't write STL; server treats missing file as empty scene
"""

# In-memory session store: session_id -> {tmpdir, chat, tempdir_obj}
sessions: dict[str, dict] = {}


def get_or_create_session(session_id: str | None) -> tuple[str, ClaudeChat]:
    """Get existing session or create a new one. Returns (session_id, chat)."""
    if session_id and session_id in sessions:
        s = sessions[session_id]
        return session_id, s["chat"]

    # Create new session
    sid = str(uuid.uuid4())
    tmpdir_obj = tempfile.TemporaryDirectory(prefix="freecad_web_")
    tmpdir = tmpdir_obj.name
    source_path = Path(tmpdir) / "source.py"
    source_path.write_text(SEED_SOURCE)

    chat = ClaudeChat(tmpdir)
    sessions[sid] = {"tmpdir": tmpdir, "chat": chat, "tempdir_obj": tmpdir_obj}
    return sid, chat


async def run_freecad_script(script: str) -> bytes | None:
    """Execute a Python script in FreeCADCmd and return the resulting STL."""
    with tempfile.TemporaryDirectory() as tmp:
        stl_path = Path(tmp) / "output.stl"
        run_py = Path(tmp) / "run.py"

        full_script = script + "\n" + EXPORT_TRAILER.format(stl_path=str(stl_path))
        run_py.write_text(full_script)

        proc = await asyncio.create_subprocess_exec(
            str(FREECAD_CMD),
            str(run_py),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError("FreeCADCmd timed out after 30s")

        if proc.returncode != 0:
            err = stderr.decode(errors="replace")
            raise RuntimeError(f"FreeCADCmd failed (exit {proc.returncode}):\n{err}")

        if not stl_path.exists():
            # Script succeeded but produced no geometry — empty scene
            return None

        return stl_path.read_bytes()


@app.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_HTML.read_text()


@app.post("/run")
async def run(request: Request):
    script = (await request.body()).decode()
    if not script.strip():
        return Response(content="Empty script", status_code=400)
    try:
        stl_bytes = await run_freecad_script(script)
    except RuntimeError as e:
        return Response(content=str(e), status_code=422, media_type="text/plain")
    if stl_bytes is None:
        return Response(status_code=204)
    return Response(content=stl_bytes, media_type="application/octet-stream")


@app.post("/chat")
async def chat(request: Request):
    """Chat endpoint — runs Claude, executes source.py, returns SSE stream."""
    body = await request.json()
    message = body.get("message", "").strip()
    session_id = body.get("session_id")

    if not message:
        return Response(content="Empty message", status_code=400)

    sid, claude = get_or_create_session(session_id)

    async def event_stream():
        try:
            # Run Claude chat in thread pool (it's blocking)
            result = await asyncio.to_thread(claude.chat, message)

            # Send response text
            yield _sse({"type": "text", "content": result["response"], "session_id": sid})

            # If source.py was edited, read it and execute
            if result["source_edited"]:
                source_path = Path(claude.project_dir) / "source.py"
                script = source_path.read_text()
                yield _sse({"type": "script", "content": script})

                # Execute in FreeCADCmd
                try:
                    stl_bytes = await run_freecad_script(script)
                    if stl_bytes is None:
                        yield _sse({"type": "clear"})
                    else:
                        stl_b64 = base64.b64encode(stl_bytes).decode()
                        yield _sse({"type": "stl", "content": stl_b64})
                except RuntimeError as e:
                    yield _sse({"type": "error", "content": str(e)})

        except Exception as e:
            yield _sse({"type": "error", "content": str(e)})

        yield _sse({"type": "done"})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse(data: dict) -> str:
    """Format a dict as an SSE event."""
    return f"data: {json.dumps(data)}\n\n"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
