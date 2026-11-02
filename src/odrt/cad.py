"""WP4 parametric concept CAD (CadQuery). Optional: requires `pip install -e .[cad]`.

Geometry is generated from the same inputs as the models: drum and cable layers
from the drivetrain, shaft diameter from structural sizing, motor envelope from
the cited motor data, belt wheels from the design ratio. This is a space claim
and load-path layout, not a manufacturing design (A-018). Units: millimetres.

Frame: X along the drum shaft, Y toward the cable exit (front), Z up.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Cited envelope for the CubeMars RO100 Standard: 113.5 mm x 36.2 mm (cubemars.com, 2026-11-02).
MOTOR_ENVELOPES_MM = {"cubemars_ro100_kv55": (113.5, 36.2)}
STANDARD_SHAFTS_MM = (12, 15, 17, 20, 25, 30, 35, 40, 45, 50)
PLATE_MARGIN_ABOVE_BORE_MM = 15.0


class CadUnavailable(RuntimeError):
    pass


def _cq():
    try:
        import cadquery as cq  # noqa: F401
    except ImportError as exc:  # optional tool: fail clearly, never silently
        raise CadUnavailable("CadQuery is not installed: run `.venv/bin/pip install -c constraints.txt "
                             "-e '.[cad]'`") from exc
    return cq


@dataclass
class Part:
    name: str
    shape: object       # cadquery Workplane
    material: str       # "shaft", "plate", "motor" or "drum"
    moving: bool


def driven_sides(opt) -> tuple:
    """One motor drives from the left end of the shaft; two motors drive both ends."""
    return (-1,) if opt.count == 1 else (-1, 1)


def standard_shaft_mm(min_d_mm: float) -> int:
    for d in STANDARD_SHAFTS_MM:
        if d >= min_d_mm:
            return d
    raise ValueError(f"shaft {min_d_mm:.1f} mm exceeds the standard size table")


def layout(st, opt, common, sizes: dict) -> dict:
    """Key layout dimensions (mm) shared by the CAD and FEA; needs no CadQuery."""
    from odrt.drivetrain import Drum
    drum = Drum(opt.architecture, common)
    motor_d, _ = MOTOR_ENVELOPES_MM.get(opt.component.id, (0.0, 0.0))
    outer_r = (drum.radii[-1] + common.cable_diameter_m / 2) * 1e3
    flange_r = outer_r + st.flange_extra_mm
    shaft_d = standard_shaft_mm(sizes["min_shaft_diameter_mm"])
    wheel_d = sizes["wheel_pitch_diameter_mm"]
    axis_z = st.base_plate_mm + max(flange_r, wheel_d / 2, motor_d / 2) + st.clearance_mm
    return {"flange_r": flange_r, "shaft_d": shaft_d, "axis_z": axis_z,
            "bearing_od": 2.0 * shaft_d + 10,
            # plate must surround the bearing bore with material above it (FEA caught a breakout)
            "plate_h": axis_z + (2.0 * shaft_d + 10) / 2 + PLATE_MARGIN_ABOVE_BORE_MM,
            "plate_depth": 2 * flange_r + 2 * st.clearance_mm, "plate_t": st.side_plate_mm,
            "base_t": st.base_plate_mm}


def build(st, opt, common, sizes: dict):
    cq = _cq()
    from odrt.drivetrain import Drum
    drum = Drum(opt.architecture, common)
    comp = opt.component
    if comp.id not in MOTOR_ENVELOPES_MM:
        raise CadUnavailable(f"no cited envelope for motor {comp.id}")
    motor_d, motor_len = MOTOR_ENVELOPES_MM[comp.id]

    core_r = opt.architecture.drum_core_radius_m * 1e3
    outer_r = (drum.radii[-1] + common.cable_diameter_m / 2) * 1e3
    flange_r = outer_r + st.flange_extra_mm
    width = drum.width_m * 1e3
    shaft_d = standard_shaft_mm(sizes["min_shaft_diameter_mm"])
    span = sizes["bearing_span_mm"]
    wheel_d = sizes["wheel_pitch_diameter_mm"]
    pinion_d = sizes["pinion_pitch_diameter_mm"]
    wheel_w = 20.0
    bearing_od, bearing_w = 2.0 * shaft_d + 10, 15.0  # 62xx-like proportions, placeholder
    axis_z = st.base_plate_mm + max(flange_r, wheel_d / 2, motor_d / 2) + st.clearance_mm
    x_bearing = span / 2
    x_wheel = x_bearing + st.wheel_overhang_mm
    centre_dist = max(wheel_d / 2 + pinion_d / 2 + 20, motor_d / 2 + shaft_d / 2 + st.motor_offset_mm)
    bracket_t = 6.0
    x_bracket = x_wheel + wheel_w / 2 + 2 + bracket_t / 2   # just outboard of the wheel
    x_motor = x_bracket + bracket_t / 2 + 1 + motor_len / 2
    shaft_len = 2 * (x_wheel + wheel_w / 2 + 1)

    def cyl_x(radius, length, x0=0.0, y0=0.0, z0=0.0):
        return (cq.Workplane("YZ").workplane(offset=x0 - length / 2).center(y0, z0)
                .circle(radius).extrude(length))

    parts = []
    drum_body = cyl_x(core_r, width, z0=axis_z)
    for side in (-1, 1):
        drum_body = drum_body.union(cyl_x(flange_r, st.flange_thickness_mm,
                                          x0=side * (width / 2 + st.flange_thickness_mm / 2), z0=axis_z))
    drum_body = drum_body.cut(cyl_x(shaft_d / 2, width + 2 * st.flange_thickness_mm + 2, z0=axis_z))
    parts.append(Part("drum", drum_body, "plate", True))
    parts.append(Part("cable layers (envelope)", cyl_x(outer_r, width - 1, z0=axis_z)
                      .cut(cyl_x(core_r, width, z0=axis_z)), "none", True))
    parts.append(Part("shaft", cyl_x(shaft_d / 2, shaft_len, z0=axis_z), "shaft", True))

    lay = layout(st, opt, common, sizes)
    plate_h, plate_depth = lay["plate_h"], lay["plate_depth"]
    for side, label in ((-1, "left"), (1, "right")):
        x_plate = side * x_bearing
        plate = (cq.Workplane("XY").box(st.side_plate_mm, plate_depth, plate_h - st.base_plate_mm, centered=(True, True, False))
                 .translate((x_plate, 0, st.base_plate_mm)))
        plate = plate.cut(cyl_x(bearing_od / 2, st.side_plate_mm + 2, x0=x_plate, z0=axis_z))
        parts.append(Part(f"side plate {label}", plate, "plate", False))
        bearing = cyl_x(bearing_od / 2, bearing_w, x0=x_plate, z0=axis_z).cut(
            cyl_x(shaft_d / 2, bearing_w + 2, x0=x_plate, z0=axis_z))
        parts.append(Part(f"bearing {label}", bearing, "shaft", False))
        if side not in driven_sides(opt):
            continue
        wheel = cyl_x(wheel_d / 2, wheel_w, x0=side * x_wheel, z0=axis_z).cut(
            cyl_x(shaft_d / 2, wheel_w + 2, x0=side * x_wheel, z0=axis_z))
        parts.append(Part(f"belt wheel {label} ({st.wheel_teeth}T)", wheel, "plate", True))
        y_motor = -centre_dist  # motors behind the drum, away from the cable exit
        motor = cyl_x(motor_d / 2, motor_len, x0=side * x_motor, y0=y_motor, z0=axis_z)
        parts.append(Part(f"motor {label} ({comp.model})", motor, "motor", True))
        pinion = cyl_x(pinion_d / 2, wheel_w, x0=side * x_wheel, y0=y_motor, z0=axis_z)
        parts.append(Part(f"pinion {label} ({st.pinion_teeth}T)", pinion, "shaft", True))
        bracket_x = side * x_bracket
        bracket = (cq.Workplane("XY").box(bracket_t, motor_d + 20, axis_z + motor_d / 2 - st.base_plate_mm,
                                          centered=(True, True, False))
                   .translate((bracket_x, y_motor, st.base_plate_mm)))
        bracket = bracket.cut(cyl_x(pinion_d / 2 + 4, 8, x0=bracket_x, y0=y_motor, z0=axis_z))
        parts.append(Part(f"motor bracket {label}", bracket, "plate", False))

    # Cable exit: fairlead roller at the front, at the height where the cable leaves the drum.
    y_front = flange_r + st.clearance_mm + 40
    exit_z = axis_z + core_r
    fairlead = cyl_x(15, 40, y0=y_front, z0=exit_z - 15 - common.cable_diameter_m * 1e3 / 2)
    parts.append(Part("fairlead roller", fairlead, "shaft", True))
    fairlead_post = (cq.Workplane("XY").box(60, 10, exit_z - 30 - st.base_plate_mm, centered=(True, True, False))
                     .translate((0, y_front + 25, st.base_plate_mm)))
    parts.append(Part("fairlead post", fairlead_post, "plate", False))

    xs = x_motor + motor_len / 2 + st.clearance_mm
    y_back = -centre_dist - motor_d / 2 - st.clearance_mm
    y_fwd = y_front + 40
    base = (cq.Workplane("XY").box(2 * xs, y_fwd - y_back, st.base_plate_mm, centered=(True, False, False))
            .translate((0, y_back, 0)))
    sx, sy = st.bolt_spacing_mm
    edge = 20.0
    if sx / 2 + edge > xs or sy / 2 + edge > (y_fwd - y_back) / 2:
        raise ValueError(f"anchor bolt spacing {sx:g} x {sy:g} mm does not fit the {2 * xs:.0f} x "
                         f"{y_fwd - y_back:.0f} mm base plate with {edge:g} mm edge margin")
    base = base.faces(">Z").workplane().pushPoints(
        [(cx, cy + (y_back + y_fwd) / 2) for cx in (-sx / 2, sx / 2) for cy in (-sy / 2, sy / 2)]).hole(12)
    parts.append(Part("base plate", base, "plate", False))

    geometry = {"shaft_diameter_mm": shaft_d, "axis_height_mm": axis_z, "envelope_mm": None,
                "drum_core_radius_mm": core_r, "drum_flange_radius_mm": flange_r, "drum_width_mm": width,
                "belt_centre_distance_mm": centre_dist, "cable_exit_height_mm": exit_z}
    return parts, geometry


def assemble(parts):
    cq = _cq()
    assy = cq.Assembly(name="odrt500_concept")
    colors = {"plate": (0.75, 0.77, 0.8), "shaft": (0.45, 0.47, 0.5), "motor": (0.2, 0.25, 0.32),
              "none": (0.85, 0.55, 0.3)}
    for p in parts:
        assy.add(p.shape, name=p.name.replace(" ", "_").replace("(", "").replace(")", ""),
                 color=cq.Color(*colors.get(p.material, (0.6, 0.6, 0.6))))
    return assy


def interferences(parts, tol_mm3: float = 1.0):
    """Pairs of distinct parts whose solids overlap by more than tol (mm^3).

    Intended contacts (shaft in drum/wheels/bearings/pinion bores, cable on drum,
    bearing in plate bore) are excluded by name.
    """
    allowed = {("drum", "shaft"), ("shaft", "bearing"), ("shaft", "belt wheel"), ("drum", "cable layers"),
               ("side plate", "bearing"), ("pinion", "motor"), ("motor bracket", "pinion"),
               ("turning sheave", "sheave axle"), ("sheave cheek", "sheave axle"), ("rubber foot", "platform pan"),
               ("stringer", "end frame"), ("stringer", "deck"), ("skirt", "end frame"), ("skirt", "deck"),
               ("end frame", "deck"), ("end frame", "platform pan"), ("skirt", "platform pan"),
               ("base plate", "platform pan"), ("sheave cheek", "sheave cross-beam"), ("sheave cross-beam", "stringer"),
               ("sheave cross-beam", "deck")}

    def kind(name):
        for k in ("cable layers", "side plate", "belt wheel", "motor bracket", "fairlead post", "fairlead roller",
                  "base plate", "turning sheave", "sheave cross-beam", "sheave cheek", "sheave axle", "rubber foot",
                  "platform pan",
                  "stringer", "skirt", "end frame", "deck", "drum", "shaft", "bearing", "motor", "pinion"):
            if name.startswith(k):
                return k
        return name

    clashes = []
    solids = [(p.name, p.shape.val()) for p in parts]
    for i in range(len(solids)):
        for j in range(i + 1, len(solids)):
            a, b = kind(solids[i][0]), kind(solids[j][0])
            if (a, b) in allowed or (b, a) in allowed:
                continue
            bb1, bb2 = solids[i][1].BoundingBox(), solids[j][1].BoundingBox()
            if (bb1.xmax < bb2.xmin or bb2.xmax < bb1.xmin or bb1.ymax < bb2.ymin or bb2.ymax < bb1.ymin
                    or bb1.zmax < bb2.zmin or bb2.zmax < bb1.zmin):
                continue
            vol = solids[i][1].intersect(solids[j][1]).Volume()
            if vol > tol_mm3:
                clashes.append((solids[i][0], solids[j][0], vol))
    return clashes


def mass_kg(parts, st, motor_mass_kg: float) -> dict:
    density = {"plate": st.plate.density_kg_m3, "shaft": st.shaft.density_kg_m3}
    out = {}
    for p in parts:
        if p.material == "motor":
            out[p.name] = motor_mass_kg
        elif p.material in density:
            out[p.name] = p.shape.val().Volume() * 1e-9 * density[p.material]
    return out


def envelope_mm(parts):
    bbs = [p.shape.val().BoundingBox() for p in parts]
    return (max(b.xmax for b in bbs) - min(b.xmin for b in bbs),
            max(b.ymax for b in bbs) - min(b.ymin for b in bbs),
            max(b.zmax for b in bbs) - min(b.zmin for b in bbs))


def round_up(x: float) -> float:
    return math.ceil(x)


def gltf_to_metres_y_up(path) -> None:
    """Wrap a GLB scene in a root node that scales mm -> m and rotates Z-up -> Y-up (glTF convention).

    The binary chunk is untouched; only the JSON chunk gains one node.
    """
    import json
    import struct
    data = open(path, "rb").read()
    json_len = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20:20 + json_len])
    rest = data[20 + json_len:]
    scene = gltf["scenes"][gltf.get("scene", 0)]
    gltf["nodes"].append({"name": "odrt500_root_mm_to_m_zup_to_yup",
                          "scale": [0.001, 0.001, 0.001],
                          "rotation": [-math.sqrt(0.5), 0.0, 0.0, math.sqrt(0.5)],  # -90 deg about X
                          "children": scene["nodes"]})
    scene["nodes"] = [len(gltf["nodes"]) - 1]
    blob = json.dumps(gltf, separators=(",", ":")).encode()
    blob += b" " * (-len(blob) % 4)
    out = (data[:12] + struct.pack("<I", len(blob)) + data[16:20] + blob + rest)
    out = out[:8] + struct.pack("<I", len(out)) + out[12:]
    open(path, "wb").write(out)


def build_platform(st, opt, common, sizes, cfg, z):
    """Floor-platform assembly (R-14): mechanism at the back, cable forward to a turning sheave, up through
    the deck port. Returns parts in the same device frame (mm); the floor is at z = -(pan + feet)."""
    cq = _cq()
    parts, geo = build(st, opt, common, sizes)
    lay = layout(st, opt, common, sizes)
    exit_z = geo["cable_exit_height_mm"]
    length, width = z["platform_length_mm"], z["platform_width_mm"]
    y_back = -(z["port_from_back_mm"] - z["drum_to_sheave_mm"])  # drum axis is at y = 0
    y_port = y_back + z["port_from_back_mm"]
    y_front = y_back + length
    deck_top = cfg.deck_h_mm
    bw, bh, wall = cfg.stringer_section_mm
    out = list(parts)
    pan = cq.Workplane("XY").box(width, length, 3, centered=(True, False, False)).translate((0, y_back, -3))
    out.append(Part("platform pan", pan, "plate", False))
    for s in (-1, 1):
        sx = s * cfg.stance_half_mm
        tube = (cq.Workplane("XZ").rect(bw, bh).rect(bw - 2 * wall, bh - 2 * wall).extrude(-length)
                .translate((sx, y_back, deck_top - cfg.deck_t_mm - bh / 2)))
        out.append(Part(f"stringer {'left' if s < 0 else 'right'}", tube, "shaft", False))
        skirt = (cq.Workplane("XY").box(4, length, deck_top - cfg.deck_t_mm, centered=(True, False, False))
                 .translate((s * (width / 2 - 2), y_back, 0)))
        out.append(Part(f"skirt {'left' if s < 0 else 'right'}", skirt, "plate", False))
    for y, label in ((y_back, "back"), (y_front - bh, "front")):
        cross = (cq.Workplane("XY").box(width - 8, bh, deck_top - cfg.deck_t_mm, centered=(True, False, False))
                 .translate((0, y, 0)))
        out.append(Part(f"end frame {label}", cross, "shaft", False))
    deck = (cq.Workplane("XY").box(width, length, cfg.deck_t_mm, centered=(True, False, False))
            .translate((0, y_back, deck_top - cfg.deck_t_mm)).edges("|Z").fillet(15.0))
    deck = deck.cut(cq.Workplane("XY").circle(22).extrude(cfg.deck_t_mm + 2).translate((0, y_port, deck_top - cfg.deck_t_mm - 1)))
    out.append(Part("deck", deck, "plate", False))
    r = cfg.sheave_r_mm
    yc, zc = y_port - r, exit_z + r
    axle_r = z["axle_mm"] / 2
    sheave = (cq.Workplane("YZ").workplane(offset=-8).center(yc, zc).circle(r).circle(axle_r + 0.5).extrude(16))
    out.append(Part("turning sheave", sheave, "plate", True))
    # sheave hangs from a cross-beam between the stringers (load path straight into the feet)
    beam_z = deck_top - cfg.deck_t_mm - bh / 2
    # the deck is too shallow for a beam above the sheave, so the beam runs just behind it and the cheeks
    # reach forward from it as brackets (adds a short moment arm in the cheeks; review)
    beam_y = yc - r - bw / 2 - 5
    beam = (cq.Workplane("YZ").rect(bw, bh).rect(bw - 2 * wall, bh - 2 * wall)
            .extrude(2 * cfg.stance_half_mm - bw).translate((-cfg.stance_half_mm + bw / 2, beam_y, beam_z)))
    out.append(Part("sheave cross-beam", beam, "shaft", False))
    gap, ct = cfg.sheave["cheek_gap_mm"], cfg.sheave["cheek_thickness_mm"]
    cheek_bottom = zc - r - 10
    cheek_y0, cheek_y1 = beam_y - bw / 2, yc + r + 10
    for s in (-1, 1):
        cheek = (cq.Workplane("XY").box(ct, cheek_y1 - cheek_y0, beam_z + bh / 2 - cheek_bottom,
                                        centered=(True, False, False))
                 .translate((s * gap / 2, cheek_y0, cheek_bottom)))
        out.append(Part(f"sheave cheek {'left' if s < 0 else 'right'}", cheek, "plate", False))
    axle =(cq.Workplane("YZ").workplane(offset=-(gap / 2 + ct)).center(yc, zc).circle(axle_r).extrude(gap + 2 * ct))
    out.append(Part("sheave axle", axle, "shaft", False))
    for cx in (-width / 2 + 25, width / 2 - 25):
        for cy in (y_back + 25, y_front - 25):
            foot = cq.Workplane("XY").circle(18).extrude(10).translate((cx, cy, -13))
            out.append(Part(f"rubber foot {cx:.0f} {cy:.0f}", foot, "none", False))
    geo = dict(geo, platform_y_back_mm=y_back, port_y_mm=y_port, sheave_centre_mm=(yc, zc))
    return out, geo
