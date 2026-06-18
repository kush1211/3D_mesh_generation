"""FastAPI backend that exposes the agent to the frontend.

- POST /run    : upload an image, stream per-node loop progress as NDJSON.
- GET  /mesh.glb : serve the latest exported mesh.
- GET  /render.png : serve the latest critique render.
- GET  /health : report readiness and whether a Gemini key is configured.

The graph itself is untouched: this just wraps `graph.astream(...)` and
serializes each node update into a JSON line the browser can read.

Run:  uvicorn src.server:app --reload   (or: python -m src.server)
"""
from __future__ import annotations

import base64
import json
import time

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from . import config
from .graph import build_graph

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
    for key in ("plan", "validation", "critique"):
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
async def run(image: UploadFile = File(...), stub: bool = Form(False)):
    data = await image.read()
    mime = image.content_type or "image/png"
    b64 = base64.b64encode(data).decode()
    use_stub = bool(stub) or not config.GEMINI_API_KEY

    async def generate():
        graph = build_graph()
        initial = {
            "image_path": image.filename or "upload",
            "image_b64": b64,
            "image_mime": mime,
            "iteration": 0,
            "max_iterations": config.MAX_ITERATIONS,
            "status": "running",
            "stub": use_stub,
        }
        yield json.dumps(
            {"type": "start", "max_iterations": config.MAX_ITERATIONS, "stub": use_stub}
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
                    yield json.dumps(_summarize(node, update), default=str) + "\n"
        except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
            yield json.dumps({"type": "error", "message": str(exc)}) + "\n"
            return

        yield json.dumps(
            {
                "type": "done",
                "status": final_state.get("status", "failed"),
                "iteration": final_state.get("iteration"),
                "validation": final_state.get("validation"),
                "critique": final_state.get("critique"),
                "has_glb": config.GLB_PATH.exists(),
                "has_render": config.RENDER_PATH.exists(),
                "ts": int(time.time()),
            },
            default=str,
        ) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


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
