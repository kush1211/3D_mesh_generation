# 2D image → validated 3D mesh agent

An autonomous agent that converts a single 2D product image into a **validated,
watertight 3D mesh** (`.glb`). A multimodal LLM (Gemini `gemini-3.1-flash-lite`,
via LangChain) plans the shape, writes **trimesh** code, critiques the rendered
result, and retries on failure. Orchestrated with **LangGraph**.

The model is connected to the **Context7 MCP server** at runtime, so during code
generation Gemini fetches *live* trimesh API docs instead of relying on memory.

## The loop

```
plan → generate → execute → validate → critique → (retry or finish)
```

| Node       | What it does |
|------------|--------------|
| `plan`     | Gemini reads the image → structured JSON plan (object type, trimesh ops, dimensions in meters). |
| `generate` | Gemini (+ Context7 tools) writes a self-contained trimesh script that exports `mesh.glb`. |
| `execute`  | Runs the script via a pluggable `Executor` (subprocess now, Docker later). |
| `validate` | Re-loads the glb in trimesh; checks `is_watertight`, `is_winding_consistent`, `euler_number`, bbox vs plan, volume. |
| `critique` | Renders the mesh headlessly (`trimesh.Scene.save_image`, matplotlib fallback) and asks Gemini if it matches the photo. |
| `finalize` | Reports success/failure. Loop caps at **4** iterations. |

## Setup

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env   # then edit .env and set GEMINI_API_KEY
```

`GEMINI_API_KEY` is read automatically by `langchain-google-genai`.
`CONTEXT7_API_KEY` is optional (higher rate limits).

## Run

```powershell
# Full pipeline (needs GEMINI_API_KEY):
.venv\Scripts\python.exe -m src.main path\to\product.jpg

# Stub mode — exercises the whole graph end-to-end with no API calls:
.venv\Scripts\python.exe -m src.main path\to\anything.png --stub
```

Outputs land in `workdir/`: `script.py`, `mesh.glb`, `render.png`.

## Frontend (meshforge)

A React UI (`frontend/`) drives the agent through a FastAPI backend that wraps the
graph and streams per-node progress.

```powershell
# 1. Backend — serves the agent at http://127.0.0.1:8000
.venv\Scripts\python.exe -m src.server

# 2a. Frontend (dev)
cd frontend; pnpm install; pnpm dev      # http://localhost:5173

# 2b. Or open the prebuilt single-file artifact
#     frontend\bundle.html  (keep the backend running)
```

Upload a product image, click **Generate mesh**, and watch plan → generate → execute →
validate → critique stream live, with the resulting `.glb` in an interactive 3D viewport
and validation/critique panels. With no `GEMINI_API_KEY`, the UI auto-runs in **stub**
mode. Backend endpoints: `POST /run` (NDJSON stream), `GET /mesh.glb`, `GET /render.png`,
`GET /health`. The `Executor` swap seam is unchanged — the server only calls the graph.

## Architecture

```
src/
  config.py            # model name, paths, limits, keys
  state.py             # AgentState (graph state)
  graph.py             # StateGraph wiring
  main.py              # CLI entrypoint
  render.py            # headless render (save_image + matplotlib fallback)
  llm/                 # Gemini-via-LangChain, Context7 MCP, schemas, prompts
  execution/           # Executor interface + SubprocessExecutor (Docker-swap seam)
  nodes/               # plan, generate, execute, validate, critique, routing, finalize
```

The three concerns — **LLM calls** (`llm/`), the **graph** (`graph.py` + `nodes/`),
and **execution** (`execution/`) — are cleanly separated. Swapping the executor
from subprocess to Docker means implementing `execution.base.Executor` and changing
one line in `nodes/execute.py`; no agent logic changes.

`trimesh.md` is the authoritative guidance for the geometry layer and is injected
into the generate prompt.
