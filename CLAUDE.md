# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An autonomous agent that converts a single 2D product image into a validated, watertight 3D mesh (`.glb`). A multimodal LLM (Gemini, via LangChain) plans the shape, writes **trimesh** code, executes it, validates the result, critiques the render against the photo, and retries on failure. Orchestrated with **LangGraph**. During code generation the model is connected to the **Context7 MCP server** so it fetches live trimesh API docs instead of relying on training memory.

## Commands

Setup and run (Windows / PowerShell — the venv interpreter is `.venv\Scripts\python.exe`):

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env   # then set GEMINI_API_KEY

# Full pipeline (needs GEMINI_API_KEY):
.venv\Scripts\python.exe -m src.main path\to\product.jpg

# Stub mode — exercises the whole graph end-to-end with NO API calls:
.venv\Scripts\python.exe -m src.main sample.png --stub
```

`src.main` auto-falls back to `--stub` when `GEMINI_API_KEY` is unset, so the graph always runs. Outputs land in `workdir/`: `script.py`, `mesh.glb`, `render.png` (gitignored).

Backend + frontend:

```powershell
.venv\Scripts\python.exe -m src.server   # FastAPI agent at http://127.0.0.1:8000
cd frontend; pnpm install; pnpm dev       # Vite UI at http://localhost:5173
# or open frontend/bundle.html (a prebuilt single-file artifact) with the backend running
cd frontend; pnpm build                   # tsc -b && vite build
cd frontend; pnpm lint                    # eslint
```

There is **no Python test suite** despite `.pytest_cache/` in `.gitignore`. Stub mode is the de-facto end-to-end smoke test.

## Architecture

The loop, wired in [src/graph.py](src/graph.py):

```
plan → generate → execute → validate → critique → finalize
  validate (pass)  → critique
  validate (fail)  → generate (retry) | finalize (capped)
  critique (match) → finalize          | generate (retry) | finalize (capped)
```

Three concerns are kept deliberately separate — keep them that way:

- **`src/llm/`** — all Gemini/LangChain calls. `models.py` builds the chat model (key auto-read from env). `schemas.py` holds Pydantic output models. `prompts.py` holds prompt text. `mcp.py` builds the Context7 MCP client.
- **`src/nodes/`** + `graph.py` — the graph. Each node is a pure `state -> partial-state-update` function. Routing decisions live in `routing.py` as conditional-edge functions.
- **`src/execution/`** — the single seam between agent logic and code execution. `base.Executor` is the ABC; `SubprocessExecutor` is the current impl. To move to Docker, implement `Executor` and change the one binding line in [src/nodes/execute.py](src/nodes/execute.py#L12). No node/graph logic changes.

State flows through `AgentState` (a `TypedDict`, [src/state.py](src/state.py)); each node returns only the keys it updates. `config.py` centralizes the model name, paths, and loop limits (`MAX_ITERATIONS = 4`, `EXEC_TIMEOUT_S`, `BBOX_REL_TOLERANCE`) — put anything tunable there, not inline in nodes.

## Conventions that matter

- **Validation is authoritative in agent code, not in the generated script.** [src/nodes/validate.py](src/nodes/validate.py) independently re-loads `mesh.glb` and checks `is_watertight`, `is_winding_consistent`, `euler_number` vs the plan, bbox extents vs planned dimensions, and positive volume. The generated script's own printed checks are advisory. On failure it composes a `feedback` string that is fed into the next `generate` attempt.

- **Structured LLM outputs use Pydantic + `with_structured_output(Model)`** ([plan.py](src/nodes/plan.py), [critique.py](src/nodes/critique.py)) — never prompt-and-parse JSON. New structured outputs go in [src/llm/schemas.py](src/llm/schemas.py).

- **`generate` is a ReAct tool-calling agent**, not a single completion. It binds Context7 MCP tools so the model fetches live trimesh docs before emitting code. The generated script must use the **trimesh API only** — never import `manifold3d` directly (it is trimesh's silent boolean backend). Code is extracted from a fenced block via regex.

- **Geometry conventions live in [trimesh.md](trimesh.md)** and are injected verbatim into the generate prompt via `config.load_trimesh_guide()`. It is the authoritative spec for the geometry layer — edit it to change geometry behavior, not the prompt strings.

- **Everything is in meters (SI).** Plans, dimensions, and validation tolerances all assume meters.

- **Stub mode** ([src/nodes/stubs.py](src/nodes/stubs.py)) provides canned plan/code/critique so every node short-circuits its LLM call when `state["stub"]` is set. When adding an LLM-calling node, add a stub branch guarded by `state.get("stub")`.

- **Rendering is headless with a fallback** ([src/render.py](src/render.py)): `trimesh.Scene.save_image` (pyglet/OpenGL) first, matplotlib 3D figure second, so the critique step always gets an image.

## Backend ↔ frontend contract

[src/server.py](src/server.py) wraps `graph.astream(..., stream_mode="updates")` and emits one NDJSON line per node update over `POST /run` (plus `GET /mesh.glb`, `GET /render.png`, `GET /health`). It does **not** touch graph logic — it only summarizes state updates. The event/type shapes are mirrored in [frontend/src/lib/agent.ts](frontend/src/lib/agent.ts); if you change what `_summarize` emits or a Pydantic schema, update the TypeScript types there to match.
