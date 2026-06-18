# meshforge — frontend

React + TypeScript UI for the 2D-image → 3D-mesh agent. Upload a product image,
watch the agent loop (plan → generate → execute → validate → critique) stream live,
and inspect the resulting `.glb` in an interactive 3D viewport with validation and
visual-critique panels.

Talks to the FastAPI backend (`src/server.py`) over HTTP/NDJSON streaming.

## Run (dev)

```powershell
# 1. Start the backend (from the project root)
..\.venv\Scripts\python.exe -m src.server        # serves http://127.0.0.1:8000

# 2. Start the frontend
pnpm install
pnpm dev                                          # http://localhost:5173
```

The API base URL is editable in the header (default `http://127.0.0.1:8000`).
If the backend has no `GEMINI_API_KEY`, the UI auto-enables **stub** mode so you can
exercise the whole flow with a canned cube.

## Single-file artifact

`bundle.html` is a self-contained build (all JS/CSS inlined). Open it directly in a
browser; it will call the backend at the API URL shown in the header. Because it
fetches `localhost`, keep the backend running.

## Stack

- React 18 + TypeScript + Vite + Tailwind + shadcn/ui
- `three` + `@react-three/fiber` + `@react-three/drei` for the WebGL viewport
- Streaming NDJSON from `POST /run`; mesh loaded from `GET /mesh.glb`
