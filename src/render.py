"""Headless mesh rendering for the critique step.

Primary path: trimesh.Scene.save_image() (pyglet/OpenGL on the desktop display)
— chosen because EGL is Linux-only and unavailable on Windows. If the GL
context can't be created, fall back to a matplotlib 3D figure so the pipeline
still produces a render to critique.
"""
from __future__ import annotations

from pathlib import Path


def _render_trimesh(glb_path: str, out_path: Path, resolution=(512, 512)) -> bool:
    import trimesh

    scene = trimesh.load(glb_path)
    if not isinstance(scene, trimesh.Scene):
        scene = trimesh.Scene(scene)
    png = scene.save_image(resolution=resolution)
    if not png:
        return False
    out_path.write_bytes(png)
    return True


def _render_matplotlib(glb_path: str, out_path: Path, resolution=(512, 512)) -> bool:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import trimesh
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    mesh = trimesh.load(glb_path, force="mesh")
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
    ax.view_init(elev=20, azim=45)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return True


def render_mesh(glb_path: str, out_path: Path, resolution=(512, 512)) -> str | None:
    """Render `glb_path` to `out_path`. Returns the path, or None on failure."""
    out_path = Path(out_path)
    for renderer in (_render_trimesh, _render_matplotlib):
        try:
            if renderer(glb_path, out_path, resolution):
                return str(out_path)
        except Exception as exc:  # noqa: BLE001 - try the next renderer
            print(f"[render] {renderer.__name__} failed: {exc}")
    return None
