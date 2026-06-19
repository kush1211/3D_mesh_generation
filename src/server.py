"""FastAPI backend that exposes the agent to the frontend.

- POST /run        : upload an image, stream per-node loop progress as NDJSON.
- GET  /runs       : list all archived runs (newest first).
- GET  /runs/{id}/mesh.glb   : fetch a specific run's mesh.
- GET  /runs/{id}/render.png : fetch a specific run's render.
- GET  /mesh.glb   : serve the latest exported mesh.
- GET  /render.png : serve the latest critique render.
- GET  /health     : report readiness and whether a Gemini key is configured.

The graph itself is untouched: this just wraps `graph.astream(...)` and
serializes each node update into a JSON line the browser can read.

Run:  uvicorn src.server:app --reload   (or: python -m src.server)
"""
from __future__ import annotations

import base64
import json
import logging
import shutil
import time
import traceback
from pathlib import Path

_LOG_FILE = Path(__file__).resolve().parent.parent / "server.log"
_LOG_FILE.touch(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from . import config
from .graph import build_graph

RUNS_DIR = config.WORKDIR / "runs"

app = FastAPI(title="2D image -> validated 3D mesh agent")

# Prototype: allow the bundled HTML artifact (any origin / file://) to call us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _summarize(node: str, update: dict) -> dict:
    """Trim a node's state update into a compact event for the browser."""
    event: dict = {"type": "node", "node": node}
    if update.get("iteration") is not None:
        event["iteration"] = update["iteration"]
    for key in ("validation", "critique"):
        if update.get(key) is not None:
            event[key] = update[key]
    if update.get("execution") is not None:
        ex = update["execution"]
        event["execution"] = {
            "ok": ex.get("ok"),
            "returncode": ex.get("returncode"),
            "timed_out": ex.get("timed_out"),
            "stderr_tail": "\n".join((ex.get("stderr") or "").strip().splitlines()[-4:]),
        }
    if update.get("code"):
        event["code_len"] = len(update["code"])
    if update.get("feedback"):
        event["feedback"] = update["feedback"]
    if update.get("status"):
        event["status"] = update["status"]
    return event


@app.post("/run")
async def run(image: UploadFile = File(...)):
    data = await image.read()
    mime = image.content_type or "image/png"
    b64 = base64.b64encode(data).decode()

    async def generate():
        log.info("run started: file=%s", image.filename)
        graph = build_graph()
        initial = {
            "image_path": image.filename or "upload",
            "image_b64": b64,
            "image_mime": mime,
            "iteration": 0,
            "max_iterations": config.MAX_ITERATIONS,
            "status": "running",
        }
        yield json.dumps(
            {"type": "start", "max_iterations": config.MAX_ITERATIONS}
        ) + "\n"

        final_state: dict = {}
        try:
            async for chunk in graph.astream(
                initial, stream_mode="updates", config={"recursion_limit": 50}
            ):
                for node, update in chunk.items():
                    if not isinstance(update, dict):
                        continue
                    final_state.update(update)
                    summary = _summarize(node, update)
                    log.info("node=%s iter=%s status=%s", node, summary.get("iteration"), summary.get("status"))
                    if summary.get("feedback"):
                        log.warning("feedback: %s", summary["feedback"][:200])
                    yield json.dumps(summary, default=str) + "\n"
        except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
            log.error("agent error: %s\n%s", exc, traceback.format_exc())
            yield json.dumps({"type": "error", "message": str(exc)}) + "\n"
            return

        ts = int(time.time())
        run_id = f"{ts}_{(image.filename or 'upload').replace(' ', '_')}"
        _archive_run(run_id, image.filename or "upload", final_state, ts)
        log.info("run done: id=%s status=%s", run_id, final_state.get("status"))

        yield json.dumps(
            {
                "type": "done",
                "status": final_state.get("status", "failed"),
                "iteration": final_state.get("iteration"),
                "validation": final_state.get("validation"),
                "critique": final_state.get("critique"),
                "has_glb": config.GLB_PATH.exists(),
                "has_render": config.RENDER_PATH.exists(),
                "run_id": run_id,
                "ts": ts,
            },
            default=str,
        ) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


def _archive_run(run_id: str, filename: str, state: dict, ts: int) -> Path | None:
    """Copy the finished mesh + render into a timestamped archive folder."""
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if config.GLB_PATH.exists():
        shutil.copy2(config.GLB_PATH, run_dir / "mesh.glb")
    if config.RENDER_PATH.exists():
        shutil.copy2(config.RENDER_PATH, run_dir / "render.png")
    for render_file in sorted(config.WORKDIR.glob("render_*.png")):
        shutil.copy2(render_file, run_dir / render_file.name)

    meta = {
        "run_id": run_id,
        "filename": filename,
        "ts": ts,
        "status": state.get("status", "failed"),
        "iteration": state.get("iteration"),
        "validation": state.get("validation"),
        "critique": state.get("critique"),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, default=str), encoding="utf-8")
    return run_dir


@app.get("/runs")
async def list_runs():
    if not RUNS_DIR.exists():
        return []
    runs = []
    for run_dir in sorted(RUNS_DIR.iterdir(), reverse=True):
        meta_file = run_dir / "meta.json"
        if not meta_file.exists():
            continue
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        meta["has_glb"] = (run_dir / "mesh.glb").exists()
        meta["has_render"] = (run_dir / "render.png").exists()
        runs.append(meta)
    return runs


@app.get("/runs/{run_id}/mesh.glb")
async def run_mesh(run_id: str):
    path = RUNS_DIR / run_id / "mesh.glb"
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path, media_type="model/gltf-binary", filename="mesh.glb")


@app.get("/runs/{run_id}/render.png")
async def run_render(run_id: str):
    path = RUNS_DIR / run_id / "render.png"
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path, media_type="image/png")


@app.get("/runs/{run_id}/render_{idx}.png")
async def run_render_view(run_id: str, idx: int):
    path = RUNS_DIR / run_id / f"render_{idx}.png"
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path, media_type="image/png")


@app.get("/mesh.glb")
async def mesh_glb():
    if not config.GLB_PATH.exists():
        return JSONResponse({"error": "no mesh yet"}, status_code=404)
    return FileResponse(
        config.GLB_PATH, media_type="model/gltf-binary", filename="mesh.glb"
    )


@app.get("/render.png")
async def render_png():
    if not config.RENDER_PATH.exists():
        return JSONResponse({"error": "no render yet"}, status_code=404)
    return FileResponse(config.RENDER_PATH, media_type="image/png")


@app.get("/health")
async def health():
    return {"ok": True, "has_key": bool(config.GEMINI_API_KEY), "model": config.MODEL_NAME}


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
