"""
parametric box - a minimal, fully parametric CadQuery example.

A 100 x 70 x 45 mm lidded enclosure:
  - open-top shell with 3 mm walls, floor and rounded vertical corners
  - four corner bosses with M3 thread-forming pilot holes
  - a 30 x 10 mm opening through the front wall
  - a 3 mm lid with four M3 clearance holes and flush countersinks

Model origin is the bottom-front-left corner.
  X = width, Y = depth, Z = height; "front" is the Y = 0 face.
Units: mm.

Run:      python box_cq.py        -> writes STL / STEP / preview data to output/
CQ-editor: open the file and press F5 to preview without exporting.
"""

import json
from pathlib import Path

import cadquery as cq
from cadquery.occ_impl.exporters.assembly import exportAssembly

# ------------------------- parameters -------------------------
W = 100.0           # outer width
D = 70.0            # outer depth
H = 45.0            # body height, floor to the open top

t = 3.0             # wall and floor thickness
corner_r = 8.0      # vertical corner radius

lid_t = 3.0         # lid plate thickness

# front-wall opening
port_w = 30.0
port_h = 10.0
port_z = 22.0       # bottom edge of the opening

# corner bosses and M3 screws
boss_d = 9.0
boss_h = 12.0
boss_inset = 12.0
pilot_d = 2.5       # thread-forming pilot in the boss
pilot_dp = 8.0      # pilot depth from the boss top
screw_clear_d = 3.3
head_cbore_d = 6.0
head_cbore_dp = 2.0

EPS = 0.01

SCREW_XY = [(boss_inset, boss_inset),
            (W - boss_inset, boss_inset),
            (boss_inset, D - boss_inset),
            (W - boss_inset, D - boss_inset)]

COLORS = {
    "body": (0.79, 0.81, 0.84),
    "lid": (0.25, 0.50, 0.75),
}
COLORS_HEX = {
    "body": "#c9ced6",
    "lid": "#3f7fbf",
}

# ------------------------- helpers -------------------------
def box(x0, x1, y0, y1, z0, z1):
    """Axis-aligned solid box from two opposite corners."""
    return (cq.Workplane("XY")
            .box(x1 - x0, y1 - y0, z1 - z0)
            .translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))


def cyl_z(cx, cy, z0, z1, d):
    """Vertical cylinder between two heights."""
    return (cq.Workplane("XY").workplane(offset=z0)
            .center(cx, cy).circle(d / 2).extrude(z1 - z0))


def rounded_box(w, d, h, r, cx, cy, cz):
    """Box with rounded vertical edges, centred at (cx, cy, cz)."""
    return (cq.Workplane("XY").box(w, d, h)
            .edges("|Z").fillet(r)
            .translate((cx, cy, cz)))

# ------------------------- parts -------------------------
def body():
    outer = rounded_box(W, D, H, corner_r, W / 2, D / 2, H / 2)

    # Cavity runs from the floor to just past the top, leaving five faces
    # and an open top. The inner radius is reduced by the wall thickness so
    # the wall stays 3 mm wide around the corner.
    inner_h = H - t + 2 * EPS
    inner = rounded_box(W - 2 * t, D - 2 * t, inner_h,
                        max(corner_r - t, 0.5),
                        W / 2, D / 2, t + inner_h / 2)
    part = outer.cut(inner)

    # Corner bosses, fused into the wall and floor.
    for sx, sy in SCREW_XY:
        part = part.union(cyl_z(sx, sy, t - EPS, t + boss_h, boss_d))

    # Thread-forming pilot holes, cut down from the boss top.
    for sx, sy in SCREW_XY:
        part = part.cut(cyl_z(sx, sy, t + boss_h - pilot_dp,
                             t + boss_h + EPS, pilot_d))

    # Front-wall opening, cut slightly past both faces so the boolean is clean.
    part = part.cut(box(W / 2 - port_w / 2, W / 2 + port_w / 2,
                        -EPS, t + EPS, port_z, port_z + port_h))
    return part


def lid():
    plate = rounded_box(W, D, lid_t, corner_r, W / 2, D / 2, H + lid_t / 2)

    for sx, sy in SCREW_XY:
        plate = plate.cut(cyl_z(sx, sy, H - EPS, H + lid_t + EPS,
                                screw_clear_d))
    for sx, sy in SCREW_XY:
        plate = plate.cut(cyl_z(sx, sy, H + lid_t - head_cbore_dp,
                                H + lid_t + EPS, head_cbore_d))
    return plate

# ------------------------- assembly -------------------------
def build_parts():
    return [("body", body()), ("lid", lid())]


def export_parts(parts):
    here = globals().get("__file__")
    out = (Path(here).resolve().parent if here else Path.cwd()) / "output"
    out.mkdir(exist_ok=True)

    print(f"front port: {port_w:.1f} x {port_h:.1f} mm at Z {port_z:.1f}")
    for name, solid in parts:
        bb = solid.val().BoundingBox()
        print(f"{name:<5} bbox = {bb.xlen:.2f} x {bb.ylen:.2f} x {bb.zlen:.2f}")
        cq.exporters.export(solid, str(out / f"{name}.stl"))
        cq.exporters.export(solid, str(out / f"{name}.step"))

    # Fused STL for printing / quick sharing.
    fused = parts[0][1]
    for _, solid in parts[1:]:
        fused = fused.union(solid)
    cq.exporters.export(fused, str(out / "box_assembly.stl"))

    # Colored STEP keeps the parts individually addressable.
    assy = cq.Assembly()
    for name, solid in parts:
        assy.add(solid, name=f"box_{name}", color=cq.Color(*COLORS[name]))
    exportAssembly(assy, str(out / "box_assembly.step"))

    # Manifest for skills/cad-code/scripts/render_assembly.py.
    manifest = [[f"output/{name}.stl", COLORS_HEX[name], 1.0]
                for name, _ in parts]
    (out / "parts.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                    encoding="utf-8")

    print(f"written to {out}")


def show_parts(parts):
    for name, solid in parts:
        show_object(solid, name=name, options={"color": COLORS[name]})


# A plain `python box_cq.py` exports; CQ-editor injects show_object and
# previews the same geometry without writing files twice.
if __name__ == "__main__":
    export_parts(build_parts())
elif "show_object" in globals():
    parts = build_parts()
    export_parts(parts)
    show_parts(parts)
