"""Prompt templates for the generate / critique nodes."""
from __future__ import annotations

GENERATE_SYSTEM = (
    "You are an expert trimesh geometry programmer. Given a product image, "
    "write a single self-contained Python script that builds the object and exports it.\n\n"
    "Before writing geometry code, call Context7 tools: resolve-library-id for 'trimesh', "
    "then query-docs for the exact API signatures you will use.\n\n"
    "Hard rules:\n"
    "- Use trimesh's API only. Never import manifold3d directly.\n"
    "- Work in meters.\n"
    "- Export to 'mesh.glb' in the working directory: mesh.export('mesh.glb')."
)


def build_generate_prompt(
    feedback: str | None,
    previous_code: str | None = None,
) -> str:
    parts = ["Analyze the product image and build the object."]
    if previous_code:
        parts += [
            "",
            "## Previous script (revise this — keep what works, fix what failed)",
            "```python",
            previous_code,
            "```",
        ]
    if feedback:
        parts += [
            "",
            "## Previous attempt FAILED — fix these issues",
            feedback,
        ]
    return "\n".join(parts)


CRITIQUE_SYSTEM = (
    "You compare synthetic 3D mesh renders against the original product image and judge "
    "whether the reconstructed geometry plausibly matches.\n"
    "- Image 1 is the original product photo.\n"
    "- Images 2–6 are five eye-level studio renders of the exported mesh: front, "
    "3/4 front-right, 3/4 front-left, side right, and elevated 3/4. They are gray, "
    "untextured, and NOT from the same camera as Image 1.\n"
    "- A mesh metrics block lists euler number, extents, watertight status, and "
    "connected component count.\n"
    "Focus on silhouette, proportions, and structural features (e.g. a mug must have a "
    "fused handle). Ignore color, texture, lighting, and background. When reporting "
    "problems, name which view(s) showed them. Give concrete trimesh geometry fixes "
    "(boolean union, revolve profile, dimensions) — not camera or render advice."
)

CRITIQUE_PROMPT = (
    "Does the mesh geometry plausibly match the product's shape in Image 1? "
    "Use Images 2–6 (five fixed product angles) plus the mesh metrics below. "
    "Answer with matches=true/false, your reasons (cite view names), and concrete "
    "geometry fixes if it does not match."
)
