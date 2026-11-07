# cad-code

An AI coding-assistant skill for generating, editing, and exporting 3D models
through code — using **OpenSCAD**, **CadQuery**, or **Build123d**.

Give the skill to an AI assistant and it can:

- Pick the right tool for the job (declarative CSG vs. Python-based
  parametric modeling)
- Write parametric, modular scripts (named dimensions, one part = one
  function/module, structured so adding a part later is a small diff)
- Install and execute the toolchain instead of only generating untested code
- Validate the result (manifold/degenerate-geometry checks, scale sanity)
  before showing anything
- Export STL / STEP as appropriate
- Render a shaded preview — single-color for simple parts, multi-color for
  assemblies — and build a **spec sheet**: the render next to a parameter
  table with real, measured dimensions, as the standard deliverable
- Handle multi-part scenes such as small architectural models (walls, roof,
  door, windows, fascia trim as distinct colored parts)
- Build 3D buildings from a **2D DXF floor plan** (wall centerlines +
  door/window layer markers) or from a plain prompt when no drawing exists

## What's inside

```
cad-code/
├── SKILL.md                   # entry point: workflow, tool selection, principles
├── references/
│   ├── openscad.md            # OpenSCAD conventions, gotchas, assembly pattern, export
│   ├── cadquery.md            # CadQuery conventions, gotchas, assembly pattern, export
│   └── build123d.md           # Build123d conventions, gotchas, assembly pattern, export
└── scripts/
    ├── render_stl.py            # headless shaded preview render, single part (matplotlib)
    ├── render_assembly.py       # headless shaded preview render, multi-part/multi-color
    ├── check_model.py           # geometry sanity checks (manifold/degenerate/scale)
    ├── spec_sheet.py            # composites render + dimensions table into one image
    ├── dxf_floorplan.py         # parses a 2D DXF floor plan into structured JSON
    └── build_from_floorplan.py  # turns that JSON into real 3D walls with openings
```

All rendering/validation scripts work off an exported STL regardless of which
of the three tools produced it, so there is one pipeline instead of three —
and no dependency on OpenGL or a display server.

**DWG note:** DWG is Autodesk's proprietary binary format. There is no
reliable open-source reader; the DXF importer covers the same floor-plan
workflow once a `.dwg` is converted/exported to `.dxf` (LibreCAD, QCAD, the
free Autodesk/ODA File Converter, or "Save As DXF" from most CAD software).

## Installing

The skill is a plain folder — no build step.

**If your AI assistant supports skill folders:** copy or link this folder into
its skills directory, using the location described in that assistant's
documentation:

```bash
cp -r skills/cad-code <your-assistant-skills-directory>/
```

**If it does not support skills:** keep the folder in the repository and tell
the assistant to read `skills/cad-code/SKILL.md` before starting a CAD task.
The workflow, tool-selection rules, and helper-script usage are all written
there.

## Requirements

Python 3.10–3.12 and:

```bash
python -m pip install cadquery CQ-editor numpy matplotlib numpy-stl ezdxf
```

`CQ-editor` is the interactive preview editor used with every model script;
launch it from the same activated environment:

```bash
cq-editor examples/parametric-box/box_cq.py
```

It needs a graphical desktop. The headless validation/rendering scripts work
without one.

Optional, depending on the workflow:

```bash
python -m pip install build123d      # Build123d models
```

OpenSCAD is a separate desktop application (Windows installer, `brew install
--cask openscad`, or the Linux distro package). If the toolchain cannot be
installed, the skill still writes the script and explains how to run it
locally.

## Output conventions

- Source script, `rows.json`, and a short model README live in the model
  directory.
- STL / STEP / preview PNG / spec sheet PNG go into `output/` and are
  regenerated, never hand-edited.
- Every model gets its own directory, so a change to one part does not
  affect another.

## Tested

The OpenSCAD, CadQuery, and Build123d paths have been run end-to-end,
including:

- A multi-part architectural model (walls, gable roof, door opening + panel,
  windows with openings + panes), validated, rendered in multi-color, and
  delivered as a spec sheet.
- A full DXF → 3D pipeline: a floor plan with wall centerlines and
  door/window layer markers parsed automatically, built into walls with
  correctly positioned openings, then extended with a roof, fascia trim, and
  door/window panels.
- Parametric mechanical enclosures, including a lidded box with M3 mounting
  bosses (see `examples/parametric-box/`).

## Known limitations

- **DWG is not supported directly** — convert to DXF first.
- `check_model.py`'s manifold check is approximate (mesh-edge-based), not a
  full CAD-kernel check. Treat the tool's own warnings (for example
  OpenSCAD's "may not be a valid 2-manifold") as authoritative.
- `render_assembly.py` uses a painter's-algorithm depth sort, not a true
  depth buffer — very busy/concave scenes can occasionally render a face in
  front of one that should occlude it. Generate a couple of views and inspect
  before delivering.
- Rotated-and-unioned slabs meeting only along an edge (for example a gable
  roof ridge) can leave a hairline non-manifold seam from floating-point
  precision. It is cosmetically invisible, but worth a cleanup pass before
  CNC/print use.
- `dxf_floorplan.py` matches openings to walls by proximity/projection, not a
  full architectural-CAD block/attribute model. It works well for simple
  layer-convention drawings and may need layer names or tolerance adjusted
  for real-world files.

## License

MIT — see [LICENSE](./LICENSE).
