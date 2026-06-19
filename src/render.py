"""Headless mesh rendering for the critique step.

Matplotlib is the primary renderer (predictable elev/azim product views).
Trimesh save_image is the fallback when matplotlib is unavailable.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from . import config

# Eye-level product views in Y-up space: (elev_deg, azim_deg, label).
_CRITIQUE_VIEWS: tuple[tuple[int, int, str], ...] = (
    (20, 0, "front"),
    (20, 45, "3/4 front-right"),
    (20, 315, "3/4 front-left"),
    (15, 90, "side right"),
    (35, 45, "elevated 3/4"),
)

# Primary thumbnail for UI / render.png (3/4 front-right).
PRIMARY_VIEW_INDEX = 1


def _prepare_display_mesh(glb_path: str):
    """Z-up trimesh geometry → Y-up, floor-aligned, centered on XZ."""
    import numpy as np
    import trimesh
    from trimesh.transformations import rotation_matrix

    mesh = trimesh.load(glb_path, force="mesh")
    mesh = mesh.copy()
    mesh.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    mesh.vertices[:, 1] -= mesh.bounds[0][1]
    cx, _, cz = mesh.centroid
    mesh.vertices[:, 0] -= cx
    mesh.vertices[:, 2] -= cz
    return mesh


def _clear_old_renders(out_dir: Path, primary_path: Path) -> None:
    for old in out_dir.glob("render_*.png"):
        old.unlink()
    if primary_path.exists():
        primary_path.unlink()


def _draw_mesh_matplotlib(ax, mesh) -> None:
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

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


def _render_matplotlib_views(
    glb_path: str, out_dir: Path, resolution: tuple[int, int]
) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mesh = _prepare_display_mesh(glb_path)
    paths: list[str] = []
    for i, (elev, azim, _) in enumerate(_CRITIQUE_VIEWS):
        fig = plt.figure(figsize=(resolution[0] / 100, resolution[1] / 100), dpi=100)
        ax = fig.add_subplot(111, projection="3d")
        _draw_mesh_matplotlib(ax, mesh)
        ax.view_init(elev=elev, azim=azim)
        out_path = out_dir / f"render_{i}.png"
        fig.savefig(out_path, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        paths.append(str(out_path))
    return paths


def _camera_transform_from_elev_azim(elev_deg: float, azim_deg: float, distance: float):
    """Build a 4x4 camera transform looking at the origin from elev/azim."""
    import numpy as np

    elev = np.radians(elev_deg)
    azim = np.radians(azim_deg)
    eye = distance * np.array(
        [
            np.cos(elev) * np.sin(azim),
            np.sin(elev),
            np.cos(elev) * np.cos(azim),
        ]
    )
    forward = -eye / np.linalg.norm(eye)
    world_up = np.array([0.0, 1.0, 0.0])
    right = np.cross(forward, world_up)
    if np.linalg.norm(right) < 1e-6:
        world_up = np.array([0.0, 0.0, 1.0])
        right = np.cross(forward, world_up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    rot = np.eye(4)
    rot[:3, 0] = right
    rot[:3, 1] = up
    rot[:3, 2] = -forward
    rot[:3, 3] = eye
    return rot


def _render_trimesh_views(
    glb_path: str, out_dir: Path, resolution: tuple[int, int]
) -> list[str]:
    import trimesh

    mesh = _prepare_display_mesh(glb_path)
    distance = float(mesh.extents.max()) * 2.5 or 1.0
    paths: list[str] = []
    for i, (elev, azim, _) in enumerate(_CRITIQUE_VIEWS):
        scene = trimesh.Scene(
            trimesh.Trimesh(vertices=mesh.vertices.copy(), faces=mesh.faces.copy())
        )
        scene.camera_transform = _camera_transform_from_elev_azim(elev, azim, distance)
        png = scene.save_image(resolution=resolution)
        if not png:
            return []
        out_path = out_dir / f"render_{i}.png"
        out_path.write_bytes(png)
        paths.append(str(out_path))
    return paths


def render_mesh_views(
    glb_path: str,
    out_dir: Path,
    primary_path: Path,
    resolution: int | None = None,
) -> list[str]:
    """Render `glb_path` from multiple angles. Returns paths to each view PNG.

    Copies the primary view (3/4 front-right) to `primary_path` for UI / render.png.
    """
    size = resolution if resolution is not None else config.CRITIQUE_RENDER_SIZE
    res = (size, size)
    out_dir = Path(out_dir)
    primary_path = Path(primary_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    _clear_old_renders(out_dir, primary_path)

    for renderer in (_render_matplotlib_views, _render_trimesh_views):
        try:
            paths = renderer(glb_path, out_dir, res)
            if paths:
                primary = paths[PRIMARY_VIEW_INDEX]
                shutil.copy2(primary, primary_path)
                return paths
        except Exception as exc:  # noqa: BLE001 - try the next renderer
            print(f"[render] {renderer.__name__} failed: {exc}")
    return []


def view_labels() -> tuple[str, ...]:
    """Human-readable label per render index (matches _CRITIQUE_VIEWS order)."""
    return tuple(label for _, _, label in _CRITIQUE_VIEWS)


def view_count() -> int:
    return len(_CRITIQUE_VIEWS)
