"""Headless mesh rendering for the critique step.

Primary path: trimesh.Scene.save_image() (pyglet/OpenGL on the desktop display)
— chosen because EGL is Linux-only and unavailable on Windows. If the GL
context can't be created, fall back to a matplotlib 3D figure so the pipeline
still produces a render to critique.
"""
from __future__ import annotations

import io
import shutil
from pathlib import Path

# Fixed studio angles (XYZ Euler degrees) — one PNG per view.
_CRITIQUE_VIEWS_DEG = [(-30, 0, 45), (-30, 0, 135)]
_VIEW_LABELS = ("3/4 front-right", "3/4 front-left")


def _centered_mesh(glb_path: str):
    import trimesh

    mesh = trimesh.load(glb_path, force="mesh")
    mesh = mesh.copy()
    mesh.vertices -= mesh.centroid
    return mesh


def _clear_old_renders(out_dir: Path, primary_path: Path) -> None:
    for old in out_dir.glob("render_*.png"):
        old.unlink()
    if primary_path.exists():
        primary_path.unlink()


def _render_trimesh_views(
    glb_path: str, out_dir: Path, resolution=(512, 512)
) -> list[str]:
    import trimesh

    import numpy as np

    mesh = _centered_mesh(glb_path)
    paths: list[str] = []
    for i, angles in enumerate(_CRITIQUE_VIEWS_DEG):
        scene = trimesh.Scene(
            trimesh.Trimesh(vertices=mesh.vertices.copy(), faces=mesh.faces.copy())
        )
        scene.set_camera(angles=np.radians(angles))
        png = scene.save_image(resolution=resolution)
        if not png:
            return []
        out_path = out_dir / f"render_{i}.png"
        out_path.write_bytes(png)
        paths.append(str(out_path))
    return paths


def _render_matplotlib_views(
    glb_path: str, out_dir: Path, resolution=(512, 512)
) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import trimesh
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    mesh = _centered_mesh(glb_path)
    views = [(20, 45), (20, 135)]
    paths: list[str] = []
    for i, (elev, azim) in enumerate(views):
        fig = plt.figure(figsize=(resolution[0] / 100, resolution[1] / 100), dpi=100)
        ax = fig.add_subplot(111, projection="3d")
        tris = mesh.vertices[mesh.faces]
        coll = Poly3DCollection(tris, alpha=1.0, edgecolor="k", linewidths=0.1)
        coll.set_facecolor((0.6, 0.7, 0.85))
        ax.add_collection3d(coll)
        bounds = mesh.bounds
        for setter, lo, hi in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), bounds[0], bounds[1]):
            setter(lo, hi)
        try:
            ax.set_box_aspect(bounds[1] - bounds[0])
        except Exception:  # noqa: BLE001 - older matplotlib
            pass
        ax.set_axis_off()
        ax.view_init(elev=elev, azim=azim)
        out_path = out_dir / f"render_{i}.png"
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        paths.append(str(out_path))
    return paths


def render_mesh_views(
    glb_path: str,
    out_dir: Path,
    primary_path: Path,
    resolution=(512, 512),
) -> list[str]:
    """Render `glb_path` from multiple angles. Returns paths to each view PNG.

    Also copies the first view to `primary_path` for the UI / legacy /render.png endpoint.
    """
    out_dir = Path(out_dir)
    primary_path = Path(primary_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    _clear_old_renders(out_dir, primary_path)

    for renderer in (_render_trimesh_views, _render_matplotlib_views):
        try:
            paths = renderer(glb_path, out_dir, resolution)
            if paths:
                shutil.copy2(paths[0], primary_path)
                return paths
        except Exception as exc:  # noqa: BLE001 - try the next renderer
            print(f"[render] {renderer.__name__} failed: {exc}")
    return []


def view_labels() -> tuple[str, ...]:
    """Human-readable label per render index (matches _CRITIQUE_VIEWS_DEG order)."""
    return _VIEW_LABELS
