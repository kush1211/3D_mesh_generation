"""Structured outputs the model must return (Pydantic -> JSON schema)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Dimensions(BaseModel):
    """Estimated real-world size in METERS (SI), per trimesh.md."""

    width_m: float = Field(description="Width in meters (X).")
    height_m: float = Field(description="Height in meters (Z, up).")
    depth_m: float = Field(description="Depth in meters (Y).")


class Plan(BaseModel):
    """Structured build plan derived from the input image."""

    object_type: str = Field(description="What the object is, e.g. 'coffee mug'.")
    description: str = Field(description="Short visual description for the builder.")
    operations: list[str] = Field(
        description=(
            "Ordered trimesh operations, drawn from: 'revolve', 'extrude', "
            "'sweep', 'primitive', 'boolean_union', 'boolean_difference'."
        )
    )
    expected_topology: str = Field(
        description="'solid' (no holes), 'one_hole' (mug/torus), or 'two_holes'."
    )
    expected_euler: int = Field(
        description="Expected Euler number: 2 for a simple solid, 0 for one handle/hole."
    )
    dimensions: Dimensions
    notes: str = Field(default="", description="Any build hints (handle placement, etc.).")


class Critique(BaseModel):
    """Visual judgement comparing the render to the input image."""

    matches: bool = Field(description="True only if the 3D render plausibly matches the image.")
    reasons: str = Field(description="Why it does or does not match.")
    suggested_fixes: str = Field(
        default="", description="Concrete geometry changes to try if it does not match."
    )
