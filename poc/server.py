"""FreeCAD Web 3D Viewer — minimal PoC server."""

import asyncio
import tempfile
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse

app = FastAPI()

FREECAD_CMD = Path(__file__).resolve().parent.parent / "build" / "debug" / "bin" / "FreeCADCmd"
INDEX_HTML = Path(__file__).resolve().parent / "index.html"

EXPORT_TRAILER = """
# --- auto-injected STL export trailer ---
import Mesh, Part

shapes = []
for obj in FreeCAD.ActiveDocument.Objects:
    if hasattr(obj, "Shape") and not obj.Shape.isNull():
        shapes.append(obj.Shape)

if shapes:
    compound = Part.makeCompound(shapes)
    mesh = Mesh.Mesh()
    for s in shapes:
        mesh.addMesh(Mesh.Mesh(s.tessellate(0.1)))
    mesh.write("{stl_path}")
else:
    raise RuntimeError("No objects with Shape found in document")
"""


async def run_freecad_script(script: str) -> bytes:
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
            err = stderr.decode(errors="replace")
            raise RuntimeError(f"No STL output produced.\nstderr: {err}")

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
    return Response(content=stl_bytes, media_type="application/octet-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
