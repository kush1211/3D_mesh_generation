"""Prompt templates for the plan / generate / critique nodes."""
from __future__ import annotations

PLAN_SYSTEM = (
    "You are a 3D reconstruction planner. Given a single product photo, you decide "
    "how to rebuild the object as a watertight 3D mesh using the trimesh library. "
    "Work entirely in METERS (SI). Pick the simplest trimesh operations that capture "
    "the shape. A radially-symmetric object (mug, bottle, vase, wheel) -> 'revolve'. "
    "A prismatic object (box, book) -> 'extrude'. A handle/tube -> 'sweep'. Fuse parts "
    "with 'boolean_union'. Set expected_euler to 2 for a simple solid, 0 for one "
    "handle/hole (e.g. a mug)."
)

PLAN_PROMPT = (
    "Analyze this product image and produce a structured build plan: the object type, "
    "the ordered trimesh operations to use, the expected topology and Euler number, and "
    "the estimated real-world dimensions in meters."
)

GENERATE_SYSTEM = (
    "You are an expert trimesh geometry programmer. You write a SINGLE self-contained "
    "Python script that builds the planned object and exports it.\n\n"
    "MANDATORY: Before writing geometry code, call the Context7 tools to fetch the CURRENT "
    "trimesh API. First call resolve-library-id for 'trimesh', then query-docs for the exact "
    "signatures of the creation/boolean functions you intend to use. Do not rely on memory.\n\n"
    "Hard rules:\n"
    "- Use trimesh's API ONLY. Never import or call manifold3d directly (it is trimesh's "
    "silent boolean backend). Use mesh.union()/.difference()/.intersection().\n"
    "- Prefer trimesh.creation.* (revolve, extrude_polygon, sweep_polygon, box, cylinder, "
    "icosphere). Keep all revolve radii >= 0.\n"
    "- Work in meters.\n"
    "- Export to the relative path 'mesh.glb' (cwd is the working dir): mesh.export('mesh.glb').\n"
    "- After building (and after every boolean), PRINT the full validation block: "
    "is_watertight, is_winding_consistent, euler_number, bounds (.tolist()), and volume.\n"
    "- If validation fails, repair with mesh.process()/merge_vertices() then trimesh.repair.* "
    "and re-validate before export.\n\n"
    "Output ONLY the Python code (optionally in a single ```python fenced block). No prose."
)


def build_generate_prompt(plan: dict, trimesh_guide: str, feedback: str | None) -> str:
    parts = [
        "Build this object as a watertight trimesh mesh and export 'mesh.glb'.",
        "",
        "## Plan (JSON)",
        str(plan),
        "",
        "## Authoritative geometry conventions (trimesh.md) — follow exactly",
        trimesh_guide,
    ]
    if feedback:
        parts += [
            "",
            "## Previous attempt FAILED — fix these issues",
            feedback,
        ]
    return "\n".join(parts)


CRITIQUE_SYSTEM = (
    "You compare a 3D mesh render against the original product image and judge whether the "
    "reconstructed geometry plausibly matches. Focus on overall silhouette, proportions, and "
    "key features (e.g. a mug must have a handle). Ignore color, texture, lighting, and "
    "background. Be strict about missing or wrong structural features."
)

CRITIQUE_PROMPT = (
    "Image 1 is the original product photo. Image 2 is a render of the generated 3D mesh. "
    "Does the 3D mesh plausibly match the product's shape? Answer with matches=true/false, "
    "your reasons, and concrete geometry fixes if it does not match."
)
