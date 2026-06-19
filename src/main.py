"""CLI entrypoint:  python -m src.main <image_path>

Loads the image, runs the agent graph, and reports the final status.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import mimetypes
import sys
from pathlib import Path

from . import config
from .graph import build_graph


async def run(image_path: str) -> dict:
    data = Path(image_path).read_bytes()
    mime = mimetypes.guess_type(image_path)[0] or "image/png"
    b64 = base64.b64encode(data).decode()

    app = build_graph()
    initial_state = {
        "image_path": image_path,
        "image_b64": b64,
        "image_mime": mime,
        "iteration": 0,
        "max_iterations": config.MAX_ITERATIONS,
        "status": "running",
    }
    print(f"Running agent on {image_path} (max_iters={config.MAX_ITERATIONS})\n")
    return await app.ainvoke(initial_state, config={"recursion_limit": 50})


def main() -> int:
    parser = argparse.ArgumentParser(description="2D image -> validated 3D mesh agent")
    parser.add_argument("image", help="Path to the input product image")
    args = parser.parse_args()

    if not Path(args.image).is_file():
        print(f"Image not found: {args.image}", file=sys.stderr)
        return 2

    if not config.GEMINI_API_KEY:
        print("GEMINI_API_KEY not set — cannot run.", file=sys.stderr)
        return 1

    final = asyncio.run(run(args.image))
    return 0 if final.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
