"""Validate node: re-load the exported glb in trimesh and check invariants.

Validation is authoritative here (in agent code), not in the generated
script's printed output — we independently re-load mesh.glb and verify
is_watertight, is_winding_consistent, euler_number, bbox extents, and volume.
On failure it composes `feedback` for the next generate attempt.
"""
from __future__ import annotations

from .. import config


def _dims_ok(extents, dimensions: dict) -> bool:
    """Compare sorted bbox extents to sorted expected dims (axis-agnostic)."""
    planned = sorted(
        [
            dimensions.get("width_m", 0.0),
            dimensions.get("height_m", 0.0),
            dimensions.get("depth_m", 0.0),
        ]
    )
    actual = sorted(float(e) for e in extents)
    for a, p in zip(actual, planned):
        if p <= 0:
            continue
        tol = max(config.BBOX_REL_TOLERANCE * p, 1e-3)
        if abs(a - p) > tol:
            return False
    return True


def validate_node(state: dict) -> dict:
    execution = state.get("execution") or {}

    if not execution.get("glb_path"):
        errors = "No mesh.glb was produced. Execution stderr:\n" + (
            execution.get("stderr") or "(none)"
        )
        print("[validate] FAILED: no glb")
        return {"validation": {"passed": False, "errors": errors}, "feedback": errors}

    import trimesh

    try:
        mesh = trimesh.load(execution["glb_path"], force="mesh")
    except Exception as exc:  # noqa: BLE001
        errors = f"Could not load exported mesh: {exc}"
        print(f"[validate] FAILED: {errors}")
        return {"validation": {"passed": False, "errors": errors}, "feedback": errors}

    extents = (mesh.bounds[1] - mesh.bounds[0]).tolist()
    checks = {
        "is_watertight": bool(mesh.is_watertight),
        "is_winding_consistent": bool(mesh.is_winding_consistent),
        "euler_number": int(mesh.euler_number),
        "expected_euler": None,
        "bounds": mesh.bounds.tolist(),
        "extents": extents,
        "volume": float(mesh.volume),
        "dims_ok": None,
    }

    problems: list[str] = []
    if not checks["is_watertight"]:
        problems.append("Mesh is NOT watertight (has holes/gaps).")
    if not checks["is_winding_consistent"]:
        problems.append("Winding is inconsistent (flipped faces).")
    if checks["volume"] <= 0:
        problems.append("Volume is non-positive (inverted normals).")

    dims = state.get("dimensions")
    if dims:
        dims_ok = _dims_ok(extents, dims)
        checks["dims_ok"] = dims_ok
        if not dims_ok:
            problems.append(
                f"Bounding-box extents {[round(e, 4) for e in extents]} m do not match expected "
                f"dimensions {dims} within tolerance."
            )

    passed = not problems
    checks["passed"] = passed
    feedback = None if passed else "Validation failed:\n- " + "\n- ".join(problems)

    print(f"[validate] {'PASSED' if passed else 'FAILED'} "
          f"(watertight={checks['is_watertight']}, winding={checks['is_winding_consistent']}, "
          f"euler={checks['euler_number']}, dims_ok={checks['dims_ok']})")
    return {"validation": checks, "feedback": feedback}
