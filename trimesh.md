---
name: trimesh-geometry
description: >
  Conventions for generating, repairing, validating, and exporting 3D meshes
  with the trimesh Python library. Use when writing code that builds a 3D mesh
  from a described shape (revolution, extrusion, sweep, primitive, or boolean
  combination) and must produce a watertight, validated result. Covers the
  creation API, the boolean backend, positioning/transforming parts, the
  validation signals to check, and the common failure modes.
---

# trimesh — geometry generation conventions

This is the single geometry library for this project. **Use trimesh's API only.**
`manifold3d` may be installed, but it exists *only* as trimesh's boolean backend —
never import or call `manifold3d` directly. Call trimesh's `.union()` / `.difference()`
/ `.intersection()` and let trimesh route to the backend.

Before writing geometry code, verify current API signatures via the Context7 MCP
server (library id is the trimesh repo). Do not trust memorized signatures for
exact argument names; trimesh's creation API has changed across versions.

## What trimesh can build natively

Prefer `trimesh.creation.*` functions over `trimesh.primitives.*` classes —
they are more flexible and are what the examples below assume.

### Revolution (lathe)

```python
trimesh.creation.revolve(
    linestring,   # (n, 2) array of [radius, height] points — all radii must be >= 0
    angle=None,   # float radians, default 2*pi (full revolution)
    sections=64,  # int — how many slices around the axis; 64 is a good default
    cap=False,    # bool — cap open ends
    transform=None,
)
```

Revolves a 2D profile (list of `[radius, height]` points) around the **Z axis**
(the 2D Y axis maps to 3D Z). Use for cups, bottles, vases, bowls, wheels, knobs —
anything radially symmetric.

**Profile rules:**
- All radii (column 0) must be `>= 0`. Negative radii are silently dropped.
- The profile is the **right-hand cross-section** only. Close it by starting and
  ending at radius=0 if you want capped ends (or set `cap=True`).
- Points are `[radius, height]` — NOT `[x, y]` in screen coords.

**Example — bottle body:**
```python
import numpy as np
import trimesh

profile = np.array([
    [0.000, 0.000],   # base center
    [0.035, 0.000],   # base edge
    [0.035, 0.080],   # straight wall
    [0.025, 0.100],   # shoulder taper
    [0.015, 0.130],   # neck
    [0.015, 0.150],   # neck top
    [0.000, 0.150],   # top center
])
body = trimesh.creation.revolve(profile, sections=64)
```

### Extrusion

```python
trimesh.creation.extrude_polygon(
    polygon,      # shapely.geometry.Polygon
    height,       # float — extrusion distance along Z (meters)
    transform=None,
    mid_plane=False,  # if True, extrudes height/2 in each direction
)
```

Sweeps a 2D shapely Polygon straight up along Z. Use for boxes, books, planks,
L-brackets, any prismatic shape with a constant cross-section.

**Example:**
```python
from shapely.geometry import Polygon
import trimesh

# Rectangular cross-section
poly = Polygon([(0, 0), (0.05, 0), (0.05, 0.03), (0, 0.03)])
slab = trimesh.creation.extrude_polygon(poly, height=0.12)
```

**Note:** `extrude_polygon` requires `shapely`. Always import shapely explicitly.
The result is watertight by default but can fail for self-intersecting polygons —
keep the polygon simple and non-self-intersecting.

### Sweep

```python
trimesh.creation.sweep_polygon(
    polygon,      # shapely.geometry.Polygon — the cross-section
    path,         # (n, 3) array — 3D path the cross-section travels along
    angles=None,  # (n,) rotation angles per step, optional
    cap=True,     # bool — cap both ends of the sweep
    connect=True, # bool — close the path into a loop
)
```

Sweeps a 2D cross-section along an arbitrary 3D path. Use for handles, tubes,
cables, bent rails. Does not handle very sharp curvature — keep path curves gentle.

**Example — C-arc handle:**
```python
from shapely.geometry import Point
import numpy as np
import trimesh

rod_section = Point(0, 0).buffer(0.005, resolution=16)  # circle, 5mm radius

n = 32
arc_r = 0.055   # must exceed body outer radius so handle projects outward
mid_z = 0.045   # mid-height of the body
angles = np.linspace(-np.pi / 2, np.pi / 2, n)
path = np.column_stack([
    np.zeros(n),
    arc_r * np.cos(angles),
    mid_z + arc_r * np.sin(angles),
])
handle = trimesh.creation.sweep_polygon(rod_section, path)
```

### Primitives

All primitives are created along the **Z axis**, centered at the origin unless
a `transform` is supplied.

```python
# Box — edge lengths [x, y, z]
trimesh.creation.box(extents=[0.05, 0.05, 0.10])

# Cylinder — along Z, centered at origin
trimesh.creation.cylinder(radius=0.03, height=0.10, sections=64)

# Cone — along Z, apex at +Z
trimesh.creation.cone(radius=0.03, height=0.08, sections=64)

# Capsule — cylinder with hemispheric caps along Z
# height = center-to-center distance of the two hemisphere centers
trimesh.creation.capsule(height=0.06, radius=0.02)

# Icosphere — evenly triangulated sphere; prefer over uv_sphere
# subdivisions=3 → 320 faces; subdivisions=4 → 1280 faces
trimesh.creation.icosphere(subdivisions=3, radius=0.05)

# Annulus (hollow cylinder) — requires EITHER height OR segment
# Calling without height raises: ValueError: either height or segment must be passed!
trimesh.creation.annulus(r_min=0.02, r_max=0.04, height=0.10, sections=64)
```

**`sections` parameter:** controls how many pie-wedge slices surround the axis.
- 64 is a good default for smooth-looking output.
- Lower values (16–32) are faster and fine for background parts.
- Do NOT leave `sections=None` for final output — trimesh may pick a very low default.

## Combining shapes — booleans

To FUSE two parts into one sealed object (e.g. a mug body + handle), use a boolean
union, not concatenation:

```python
combined = part_a.union(part_b)         # fuse into one watertight solid
result   = solid.difference(tool)       # subtract (cut a hole)
result   = a.intersection(b)            # keep overlapping volume only
```

`trimesh.util.concatenate([a, b])` only stacks two separate shells into one object —
it does NOT merge them into a watertight solid. Use it only when the parts are
genuinely separate and watertightness across the join is not required.

Booleans are the most common source of non-watertight output. Always re-validate
after a boolean.

## Positioning parts (translations & rotations)

Parts created by `trimesh.creation.*` are centered at the origin by default.
You must position them before combining.

```python
# Translate — move a mesh by an offset vector [x, y, z]
mesh.apply_translation([0.0, 0.0, 0.05])    # move 5 cm up along Z

# Rotate — build a (4,4) homogeneous matrix and apply it
import trimesh.transformations as tf
rot = tf.rotation_matrix(np.pi / 2, [1, 0, 0])   # 90° around X axis
mesh.apply_transform(rot)

# Rotate + translate in one step using a 4×4 matrix
T = tf.rotation_matrix(angle, axis, point)   # point = pivot, default origin
mesh.apply_transform(T)

# Center a mesh on its own centroid before positioning
mesh.apply_translation(-mesh.center_mass)
```

**Positioning checklist before boolean union:**
1. Build each part at the origin.
2. Translate/rotate each part into its final position.
3. Verify that parts meant to fuse **overlap** — not just touch.
   A surface-only contact leaves a zero-thickness seam that booleans fail on.
4. Call `.union()`, then `.process()`, then re-validate.

## Units

Work in **meters** throughout (SI). A coffee mug is ~0.097 m tall, ~0.040 m radius.
Keep all dimensions in meters so downstream physics/scale stays consistent.

## Validation — what to check after building

A mesh that exports without error is NOT necessarily valid. After every build
(and after every boolean), check and print all of these:

```python
print("watertight:", mesh.is_watertight)          # must be True
print("winding:",    mesh.is_winding_consistent)  # must be True
print("euler:",      mesh.euler_number)           # 2=solid, 0=one hole, -2=two holes
print("volume:",     mesh.volume)                 # must be positive
print("bounds:",     mesh.bounds.tolist())        # check real-world extents
```

**Euler characteristic reference:**
- `2` — simple solid, no through-holes (sphere, box, bottle, bowl)
- `0` — one handle or through-hole (mug with handle, torus, bucket with handle)
- `-2` — two through-holes

**Important:** `is_watertight: True` alone does NOT mean the shape is correct. A
broken/buried handle can still report watertight. Always check Euler number AND
bounding-box projection together to catch a structurally-wrong-but-sealed mesh.

A handle that doesn't extend past the body radius in the bounds means the union
swallowed it — the arc_radius was too small.

## Repair — when validation fails

Try cheap fixes first, in order:

1. `mesh.process()` / `mesh.merge_vertices()` — basic cleanup.
2. `trimesh.repair.fill_holes(mesh)`, `trimesh.repair.fix_winding(mesh)`,
   `trimesh.repair.fix_inversion(mesh)`, `trimesh.repair.fix_normals(mesh)` —
   targeted first-pass repairs.
3. `pymeshfix` (if installed) — the heavy option: full reconstruction to a
   watertight mesh. Use only when trimesh.repair can't recover it, since it can
   alter geometry.

If repair changes the mesh, re-run the full validation block afterward.

## Export

```python
mesh.export('mesh.glb')   # preferred — compact, widely viewable
mesh.export('mesh.stl')   # for downstream tools that require STL
```

Always write the final mesh to a known path and print it so the caller can pick it up.

## Canonical handle recipe (mug, cup, bag, etc.)

A mug handle is a torus-sector swept along a C-shaped arc. This is the ONLY
reliable approach — do NOT use `annulus`, `cylinder`, or a hand-built vertex
ring for a handle:

```python
import numpy as np
import trimesh
from shapely.geometry import Point

# --- body (revolve) ---
profile = np.array([
    [0.000, 0.000],
    [0.040, 0.000],
    [0.040, 0.090],
    [0.038, 0.095],
    [0.000, 0.095],
])
body = trimesh.creation.revolve(profile, sections=64)

# --- handle: sweep a small circle along a C-arc ---
rod_section = Point(0, 0).buffer(0.005, resolution=16)   # 5 mm radius

n_steps = 32
arc_radius = 0.053          # must be > body outer radius (0.040) so it projects out
mid_z = 0.045               # half of body height
angles = np.linspace(-np.pi / 2, np.pi / 2, n_steps)   # 180° C
path = np.column_stack([
    np.zeros(n_steps),
    arc_radius * np.cos(angles),
    mid_z + arc_radius * np.sin(angles),
])
handle = trimesh.creation.sweep_polygon(rod_section, path)

# --- fuse with boolean union (NOT concatenate) ---
combined = body.union(handle)
combined.process()

# --- validate ---
print("watertight:", combined.is_watertight)
print("winding:",    combined.is_winding_consistent)
print("euler:",      combined.euler_number)   # must be 0 for one-hole object
print("volume:",     combined.volume)
print("bounds:",     combined.bounds.tolist())

combined.export('mesh.glb')
print("exported mesh.glb")
```

Key constraints for the handle to fuse:
- The arc endpoints must **overlap** the body wall (arc_radius ≥ body_outer_radius).
  If the arc just touches the surface, boolean precision can leave a gap.
- The cross-section must be a `shapely.geometry.Polygon` (not a trimesh).
- After `union`, always run `combined.process()` before validating.

## Common failure modes (seen in practice)

- **`trimesh.creation.annulus` requires `height` OR `segment`** — calling it without
  either raises `ValueError: either height or segment must be passed!`. If you need
  a hollow tube, pass `height=<value>`. Better: use `sweep_polygon` for handles instead.

- **Negative or zero revolve radius** — revolve uses only radii >= 0. Points with
  negative radius are silently dropped, producing a broken or missing surface.
  Keep all profile radii >= 0 and verify the profile shape before calling revolve.

- **Buried boolean part** — translating an added part too far into the body so the
  union absorbs it. Symptom: Euler not what you expect, bounds don't extend past
  the body. Fix: position the part so it clearly overlaps the surface but mostly
  projects outward.

- **Euler -2 after union** — two disconnected shells were union'd but didn't actually
  fuse (arc didn't overlap the body). Increase arc_radius until the handle ends
  clearly penetrate the body wall, then re-union.

- **Parts only touching, not overlapping** — a zero-thickness contact at a surface
  is not enough for a clean boolean. Parts must genuinely interpenetrate by at least
  ~1 mm before the boolean to guarantee fusion.

- **Profile crossing the axis on revolve** — keep all radii >= 0.

- **Missing shapely** — `extrude_polygon` / `sweep_polygon` need shapely. Ensure it's
  installed before using polygon-based creation.

- **Non-watertight after sweep** — open-ended sweeps don't cap automatically unless
  `cap=True`. Check watertightness and set `cap=True` or fill end caps if needed.

- **Inverted normals after boolean** — run `trimesh.repair.fix_inversion` /
  `fix_normals` and re-check that volume is positive.

- **`sections=None` giving too-low default** — always pass an explicit `sections`
  value (64 recommended) for any revolve/cylinder/cone to avoid faceted output.

- **Positioning error before boolean** — always verify with `mesh.bounds` that the
  part to be fused actually extends outside the base mesh before calling `.union()`.

## Build-then-verify discipline

1. Build each part with the right creation function.
2. Position parts with `apply_translation` / `apply_transform` so they overlap correctly.
3. Boolean-union them one at a time; re-validate after each union.
4. Run the full validation block (watertight, winding, euler, bounds, volume) and print it.
5. If anything fails, repair, then re-validate.
6. Export and print the output path.

Never report success on export alone — success means the validation block passed
AND the bounds/topology match the intended shape.
