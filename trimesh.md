---
name: trimesh-geometry
description: >
  Conventions for generating, repairing, validating, and exporting 3D meshes
  with the trimesh Python library. Use when writing code that builds a 3D mesh
  from a described shape (revolution, extrusion, sweep, primitive, or boolean
  combination) and must produce a watertight, validated result. Covers the
  creation API, the boolean backend, the validation signals to check, and the
  common failure modes.
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

These cover the shape vocabulary for this project. Prefer the `trimesh.creation`
functions over the `trimesh.primitives` classes — they are more flexible and are
what the examples below assume.

- **Revolution (lathe):** `trimesh.creation.revolve(linestring, ...)` — rotate a 2D
  profile (list of [radius, height] points) around an axis. Use for cups, bottles,
  vases, bowls, wheels, knobs — anything radially symmetric.
- **Extrusion:** `trimesh.creation.extrude_polygon(polygon, height)` — sweep a 2D
  polygon straight up. Use for boxes, books, planks, shelves. Needs a shapely
  polygon as input (shapely is a required dependency for this).
- **Sweep:** `trimesh.creation.sweep_polygon(polygon, path)` — sweep a 2D cross-section
  along an arbitrary 3D path. Use for handles, tubes, cables, bent rails.
- **Primitives:** `trimesh.creation.box`, `cylinder`, `icosphere`, `cone`, `capsule`,
  `annulus`. Use `icosphere` rather than UV spheres — it triangulates more evenly.
- **Custom mesh:** `trimesh.Trimesh(vertices=..., faces=...)` — only as a last resort
  when no creation function fits. Hand-built vertex/face lists are error-prone and
  frequently non-watertight.

## Combining shapes — booleans

To FUSE two parts into one sealed object (e.g. a mug body + handle), use a boolean
union, not concatenation:

- Union: `combined = part_a.union(part_b)`
- Difference (cut a hole): `result = solid.difference(tool)`
- Intersection: `result = a.intersection(b)`

`trimesh.util.concatenate([a, b])` only stacks two separate shells into one object —
it does NOT merge them into a watertight solid. Use it only when the parts are
genuinely separate and watertightness across the join is not required.

Booleans are the most common source of non-watertight output. Always re-validate
after a boolean.

## Units

Work in **meters** throughout (SI). A coffee mug is ~0.097 m tall, ~0.04 m radius.
Keep all dimensions in meters so downstream physics/scale stays consistent.

## Validation — what to check after building

A mesh that exports without error is NOT necessarily valid. After every build
(and after every boolean), check and print all of these:

- `mesh.is_watertight` — must be `True`. A non-watertight mesh has holes/gaps.
- `mesh.is_winding_consistent` — must be `True`. Inconsistent winding = flipped faces.
- `mesh.euler_number` — a topology signal. A simple solid (sphere-like, no holes) = 2.
  An object with ONE handle/hole (a mug, a torus) = 0. Two holes = -2.
  Use this to confirm the topology matches intent: a mug WITH a handle should be 0;
  if it comes back 2, the handle did not actually fuse to the body.
- `mesh.bounds` — print min/max corners. Confirm real-world dimensions match the plan,
  and (critically) that an attached part actually projects outward rather than being
  buried inside the body. A handle that doesn't extend past the body radius means the
  union swallowed it.
- `mesh.volume` — sanity-check it's positive and plausible. Negative volume means
  inverted normals.

**Important:** `is_watertight: True` alone does NOT mean the shape is correct. A
broken/buried handle can still report watertight. Always check Euler number AND
bounding-box projection together to catch a structurally-wrong-but-sealed mesh.

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

- `mesh.export('mesh.glb')` — preferred for inspection/rendering (compact, widely viewable).
- `mesh.export('mesh.stl')` — for any downstream tool that wants STL.

Always write the final mesh to a known path and print it so the caller can pick it up.

## Common failure modes (seen in practice)

- **Buried boolean part:** translating an added part too far into the body so the
  union absorbs it. Symptom: Euler not what you expect, bounds don't extend past
  the body. Fix: position the part so it clearly overlaps the surface but mostly
  projects outward; for a handle, build it as an open C-arc whose ends touch the
  wall, not a full ring centered in the wall.
- **Profile crossing the axis on revolve:** revolve uses only the positive-X side of
  the profile; points with negative radius get dropped. Keep all radii >= 0.
- **Missing shapely:** `extrude_polygon` / `sweep_polygon` need shapely. Ensure it's
  installed before using polygon-based creation.
- **Non-watertight after sweep:** open-ended sweeps don't cap. Check watertightness
  and fill end caps if needed.
- **Inverted normals after boolean:** run `trimesh.repair.fix_inversion` /
  `fix_normals` and re-check that volume is positive.

## Build-then-verify discipline

1. Build the shape with the right creation function.
2. If combining parts, union them.
3. Run the full validation block (watertight, winding, euler, bounds, volume) and print it.
4. If anything fails, repair, then re-validate.
5. Export and print the output path.

Never report success on export alone — success means the validation block passed
AND the bounds/topology match the intended shape.
