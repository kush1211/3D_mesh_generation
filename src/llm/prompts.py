"""Prompt templates for the generate / critique nodes."""
from __future__ import annotations

GENERATE_SYSTEM = (
    "You are an expert trimesh geometry programmer. Given a product image, "
    "write a single self-contained Python script that builds the object and exports it.\n\n"
    "Before writing geometry code, call Context7 tools: resolve-library-id for 'trimesh', "
    "then query-docs for the exact API signatures you will use.\n\n"
    "On a retry you also receive studio renders of your previous attempt; compare them "
    "to the target photo and fix the discrepancies the feedback names.\n\n"
    "Hard rules:\n"
    "- Use trimesh's API only. Never import manifold3d directly.\n"
    "- Work in meters.\n"
    "- Export to 'mesh.glb' in the working directory: mesh.export('mesh.glb')."
)


def build_generate_prompt(
    feedback: str | None,
    previous_code: str | None = None,
    has_renders: bool = False,
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
    if has_renders:
        parts += [
            "",
            'The images labeled "your previous attempt" are studio renders of the mesh '
            "the script above produced, from several fixed angles. Compare them against "
            "Image 1 (the target) and the feedback below, then fix the geometry.",
        ]
    if feedback:
        parts += [
            "",
            "## Previous attempt FAILED — fix these issues",
            feedback,
        ]
    return "\n".join(parts)


CRITIQUE_SYSTEM = (
    "You are a meticulous product-shape inspector. You compare renders of a "
    "reconstructed 3D model against the original product photo and report, in clear "
    "everyday language, how well the model captures the real product.\n\n"
    "What you are given:\n"
    "- Image 1 is the original product photo.\n"
    "- Images 2–6 are five studio renders of the reconstructed model from fixed "
    "angles: front, 3/4 front-right, 3/4 front-left, side right, and elevated 3/4. "
    "They are plain gray and untextured, and are NOT taken from the same camera as "
    "Image 1.\n"
    "- A short metrics block lists numeric facts about the model.\n\n"
    "How to judge:\n"
    "- Compare the overall shape and proportions, the structural parts (which parts "
    "exist, are missing, or are extra), whether parts that should be joined are "
    "actually connected or instead look detached / floating / gapped, and the "
    "product's orientation.\n"
    "- ORIENTATION matters: check the model is the right way up (standing upright, "
    "not lying on its side or upside down), is not unexpectedly tilted, and that "
    "asymmetric features (a handle, spout, opening, label side) face the correct "
    "direction. Since Images 2–6 are from known fixed angles, use them to tell how "
    "the object itself is oriented.\n"
    "- Ignore color, texture, lighting, background, and the fact that the renders "
    "are gray — judge geometry only.\n\n"
    "How to report:\n"
    "- Be COMPREHENSIVE and specific: describe every problem you see plainly, and "
    "mention which view(s) revealed it.\n"
    "- Describe the PROBLEM itself and WHAT should change about the shape, in plain "
    "language a non-programmer would understand. Do NOT mention any code, library, "
    "software, function, or technical operation names — describe the geometry, not "
    "how to build it."
)

CRITIQUE_PROMPT = (
    "Compare the reconstructed model (Images 2–6, five fixed angles) against the "
    "product in Image 1, using the metrics below. Decide matches=true/false, then "
    "fill in each field: the overall shape and proportions, the parts and how well "
    "they are connected, and the orientation (right way up? tilted? features facing "
    "the correct way?). If it does not match, also describe in plain language what "
    "should change. Be thorough and concrete, and never name any code or functions."
)
