"""Canned products used in --stub mode so the graph runs end-to-end with no API.

The stub plan/code build a watertight 0.1 m cube; the stub critique approves it,
so a stub run exercises the full happy path plan->generate->execute->validate->
critique->finalize and terminates with status='success'.
"""
from __future__ import annotations

STUB_PLAN = {
    "object_type": "box (stub)",
    "description": "Placeholder cube used to exercise the graph without an LLM.",
    "operations": ["primitive"],
    "expected_topology": "solid",
    "expected_euler": 2,
    "dimensions": {"width_m": 0.1, "height_m": 0.1, "depth_m": 0.1},
    "notes": "stub",
}

STUB_CODE = """\
import trimesh

mesh = trimesh.creation.box(extents=[0.1, 0.1, 0.1])

# Basic cleanup per trimesh.md.
mesh.merge_vertices()

mesh.export('mesh.glb')

print('is_watertight', mesh.is_watertight)
print('is_winding_consistent', mesh.is_winding_consistent)
print('euler_number', mesh.euler_number)
print('bounds', mesh.bounds.tolist())
print('volume', mesh.volume)
"""
