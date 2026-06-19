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


def build_generate_prompt(feedback: str | None) -> str:
    parts = ["Analyze the product image and build the object."]
    if feedback:
        parts += [
            "",
            "## Previous attempt FAILED — fix these issues",
            feedback,
        ]
    return "\n".join(parts)


CRITIQUE_SYSTEM = (
    "You compare synthetic 3D mesh renders against the original product image and judge "
    "whether the reconstructed geometry plausibly matches. Images 2+ are separate fixed-angle "
    "studio renders of the exported mesh (gray, no texture) — NOT photos from the same camera "
    "as Image 1. Focus on overall silhouette, proportions, and key structural features "
    "(e.g. a mug must have a handle). Ignore color, texture, lighting, background, and camera "
    "viewpoint differences. Be strict about missing or wrong structural features."
)

CRITIQUE_PROMPT = (
    "Image 1 is the original product photo. Images 2+ are separate renders of the exported "
    "3D mesh from different fixed angles. Does the mesh geometry plausibly match the product's "
    "shape? Answer with matches=true/false, your reasons, and concrete geometry fixes if it "
    "does not match."
)
