"""Presentation model of the concept: detailed parts, enclosure proposal, handle.

Built on the same layout numbers as the engineering CAD (cad.layout / cad.build)
so it stays consistent with the models. Detail is visual: tooth profiles, belts,
wound cable, bolts and the enclosure are not engineered. Device frame in mm:
X along the shaft, Y toward the cable exit, Z up. Converted to glTF metres Y-up
on export.

Groups: "static" parts never move; "drum" rotates about the shaft axis;
"motor_left/right" rotate about each motor axis (pinion and outrunner can).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from odrt import cad
from odrt.gltf import Material

MATERIALS = {
    "graphite": Material("graphite anodised aluminium", (0.035, 0.037, 0.04, 1.0), 0.6, 0.45),
    "fascia": Material("satin light grey", (0.55, 0.56, 0.57, 1.0), 0.0, 0.55),
    "glass": Material("frosted smoked cover", (0.32, 0.34, 0.36, 0.45), 0.0, 0.32, transmission=0.6),
    "alu": Material("brushed aluminium", (0.80, 0.80, 0.80, 1.0), 1.0, 0.32),
    "steel": Material("steel", (0.62, 0.62, 0.62, 1.0), 1.0, 0.25),
    "dark_steel": Material("black oxide steel", (0.05, 0.05, 0.05, 1.0), 0.9, 0.4),
    "motor": Material("motor can", (0.08, 0.09, 0.1, 1.0), 0.8, 0.35),
    "copper": Material("copper winding", (0.72, 0.35, 0.17, 1.0), 1.0, 0.35),
    "belt": Material("belt rubber", (0.02, 0.02, 0.02, 1.0), 0.0, 0.8),
    "rope": Material("rope", (0.75, 0.73, 0.68, 1.0), 0.0, 0.7),
    "rubber": Material("rubber", (0.03, 0.03, 0.03, 1.0), 0.0, 0.9),
    "light": Material("status light", (0.6, 0.75, 0.68, 1.0), 0.0, 0.4, emissive=(0.35, 0.55, 0.45)),
    "skin": Material("mannequin", (0.62, 0.6, 0.57, 1.0), 0.0, 0.6),
    "floor": Material("floor", (0.3, 0.29, 0.28, 1.0), 0.0, 0.85),
    "wall": Material("wall", (0.7, 0.69, 0.67, 1.0), 0.0, 0.9),
}


@dataclass
class VPart:
    name: str
    shape: object      # cadquery Workplane, device frame mm
    material: str
    group: str         # "static", "drum", "motor_left", "motor_right"


def _toothed(cq, teeth, pitch_mm, width, depth=1.2):
    """Extruded timing-pulley outline along X (approximate HTD rounded notches)."""
    r_pitch = teeth * pitch_mm / (2 * math.pi)
    r_out = r_pitch - 0.57  # HTD pitch line offset
    n = teeth * 12
    pts = []
    for k in range(n):
        th = 2 * math.pi * k / n
        phase = (th * teeth / (2 * math.pi)) % 1.0
        notch = max(0.0, math.cos((phase - 0.5) * math.pi * 2.4)) if 0.08 < phase < 0.92 else 0.0
        r = r_out - depth * notch
        pts.append((r * math.cos(th), r * math.sin(th)))
    return cq.Workplane("YZ").polyline(pts).close().extrude(width).translate((-width / 2, 0, 0)), r_out


def _belt(cq, c1, r1, c2, r2, thick, width):
    """Closed belt around two pulleys (centres in the YZ plane), extruded along X."""
    def loop(ra, rb):
        (y1, z1), (y2, z2) = c1, c2
        d = math.hypot(y2 - y1, z2 - z1)
        base = math.atan2(z2 - z1, y2 - y1)
        phi = math.acos((ra - rb) / d)
        a1, a2 = base + phi, base - phi
        p = lambda c, r, a: (c[0] + r * math.cos(a), c[1] + r * math.sin(a))  # noqa: E731
        w = (cq.Workplane("YZ").moveTo(*p(c1, ra, a1)).lineTo(*p(c2, rb, a1))
             .threePointArc(p(c2, rb, base), p(c2, rb, a2)).lineTo(*p(c1, ra, a2))
             .threePointArc(p(c1, ra, base + math.pi), p(c1, ra, a1)).close())
        return w.extrude(width)
    return loop(r1 + thick, r2 + thick).cut(loop(r1, r2)).translate((-width / 2, 0, 0))


def _hex_bolt(cq, x, y, z, size=8.0, height=5.0, axis="Z"):
    w = {"Z": "XY", "X": "YZ", "Y": "XZ"}[axis]
    b = cq.Workplane(w).polygon(6, size * 1.8 / math.cos(math.pi / 6)).extrude(height)
    b = b.edges(">Z" if axis == "Z" else (">X" if axis == "X" else ">Y")).chamfer(0.6)
    return b.translate((x, y, z))


def build(st, opt, common, sizes):
    cq = cad._cq()
    from odrt.drivetrain import Drum
    lay = cad.layout(st, opt, common, sizes)
    drum = Drum(opt.architecture, common)
    motor_d, motor_len = cad.MOTOR_ENVELOPES_MM[opt.component.id]
    d_cable = common.cable_diameter_m * 1e3
    core_r = opt.architecture.drum_core_radius_m * 1e3
    flange_r, shaft_d, axis_z = lay["flange_r"], lay["shaft_d"], lay["axis_z"]
    width = drum.width_m * 1e3
    span = sizes["bearing_span_mm"]
    x_bearing = span / 2
    x_wheel = x_bearing + st.wheel_overhang_mm
    wheel_w = 20.0
    pinion_pd = sizes["pinion_pitch_diameter_mm"]
    wheel_pd = sizes["wheel_pitch_diameter_mm"]
    centre = max(wheel_pd / 2 + pinion_pd / 2 + 20, motor_d / 2 + shaft_d / 2 + st.motor_offset_mm)
    y_motor = -centre
    x_bracket = x_wheel + wheel_w / 2 + 2 + 3
    x_motor = x_bracket + 3 + 1 + motor_len / 2
    parts = []

    def cyl(r, length, x0=0.0, y0=0.0, z0=axis_z):
        return cq.Workplane("YZ").workplane(offset=x0 - length / 2).center(y0, z0).circle(r).extrude(length)

    # --- drum group (rotates about the shaft axis)
    body = cyl(core_r, width)
    for s in (-1, 1):
        fl = cyl(flange_r, st.flange_thickness_mm, x0=s * (width / 2 + st.flange_thickness_mm / 2))
        body = body.union(fl)
    body = body.edges("%CIRCLE").fillet(0.8)
    parts.append(VPart("drum", body, "alu", "drum"))
    turns = 9  # wound cable (visual): one layer from the left flange, numpy tube (see wrap_mesh)
    wrap_spec = {"turns": turns, "radius": core_r + d_cable / 2, "pitch": d_cable, "tube_r": d_cable / 2 * 0.95,
                 "x0": -width / 2 + d_cable / 2 + 0.5}
    shaft_len = 2 * (x_wheel + wheel_w / 2 + 1)
    parts.append(VPart("shaft", cyl(shaft_d / 2, shaft_len).faces("<X or >X").chamfer(1.0), "steel", "drum"))
    for s, label in ((-1, "left"), (1, "right")):
        wheel, r_out = _toothed(cq, st.wheel_teeth, st.belt_pitch_mm, wheel_w)
        wheel = wheel.translate((s * x_wheel, 0, axis_z))
        holes = (cq.Workplane("YZ").workplane(offset=s * x_wheel - wheel_w)
                 .center(0, axis_z).polarArray(r_out * 0.6, 0, 360, 6).circle(r_out * 0.17).extrude(2 * wheel_w))
        wheel = wheel.cut(holes)
        for fs in (-1, 1):  # belt guide flanges
            wheel = wheel.union(cyl(r_out + 2.5, 1.5, x0=s * x_wheel + fs * (wheel_w / 2 + 0.75)))
        parts.append(VPart(f"wheel {label}", wheel, "alu", "drum"))
        parts.append(VPart(f"wheel hub {label}", cyl(shaft_d / 2 + 9, wheel_w + 10, x0=s * x_wheel), "dark_steel", "drum"))

    # --- motors (outrunner can + pinion rotate; stator flange static)
    for s, label in ((-1, "left"), (1, "right")):
        group = f"motor_{label}"
        pin, pin_r = _toothed(cq, st.pinion_teeth, st.belt_pitch_mm, wheel_w)
        pin = pin.translate((s * x_wheel, y_motor, axis_z))
        for fs in (-1, 1):
            pin = pin.union(cyl(pin_r + 2.5, 1.5, x0=s * x_wheel + fs * (wheel_w / 2 + 0.75), y0=y_motor))
        parts.append(VPart(f"pinion {label}", pin, "steel", group))
        parts.append(VPart(f"motor shaft {label}", cyl(5, abs(x_motor - x_wheel) + 10,
                                                        x0=s * (x_wheel + x_motor) / 2, y0=y_motor), "steel", group))
        can_len = motor_len * 0.7
        can_x = s * (x_motor + motor_len / 2 - can_len / 2)
        can = cyl(motor_d / 2, can_len, x0=can_x, y0=y_motor).edges("%CIRCLE").fillet(2.0)
        face = (cq.Workplane("YZ").workplane(offset=can_x + s * can_len / 2 - 3).center(y_motor, axis_z)
                .polarArray(motor_d * 0.3, 0, 360, 8).slot2D(motor_d * 0.2, 7, 0).extrude(6))
        can = can.cut(face)
        parts.append(VPart(f"motor can {label}", can, "motor", group))
        stator = cyl(motor_d / 2 * 0.86, motor_len * 0.3, x0=s * (x_motor - motor_len / 2 + motor_len * 0.15), y0=y_motor)
        parts.append(VPart(f"motor stator {label}", stator, "copper", "static"))
        belt = _belt(cq, (0.0, axis_z), r_out_wheel(st), (y_motor, axis_z), pin_r, 1.8, wheel_w - 4)
        parts.append(VPart(f"belt {label}", belt.translate((s * x_wheel, 0, 0)), "belt", "static"))

    # --- frame
    lay_parts, _ = cad.build(st, opt, common, sizes)
    for p in lay_parts:
        if p.name.startswith("side plate"):
            parts.append(VPart(p.name, p.shape.edges("|Y").fillet(3.0), "alu", "static"))
        elif p.name.startswith("motor bracket"):
            parts.append(VPart(p.name, p.shape.edges("|Y").fillet(2.0), "alu", "static"))
        elif p.name.startswith("base plate"):
            parts.append(VPart(p.name, p.shape.edges("|Z").fillet(8.0), "dark_steel", "static"))
            base_bb = p.shape.val().BoundingBox()
        elif p.name.startswith("fairlead"):
            parts.append(VPart(p.name, p.shape, "steel" if "roller" in p.name else "alu", "static"))
    for s, label in ((-1, "left"), (1, "right")):  # flanged bearing units on the outer faces
        x_out = s * (x_bearing + st.side_plate_mm / 2 + 6)
        unit = (cq.Workplane("YZ").workplane(offset=x_out - 6).center(0, axis_z).rect(lay["bearing_od"] + 24,
                lay["bearing_od"] + 24).extrude(12).edges("|X").fillet(8.0))
        unit = unit.union(cyl(lay["bearing_od"] / 2 + 4, 20, x0=x_out + s * 6)).cut(cyl(shaft_d / 2 + 0.5, 60, x0=x_out))
        parts.append(VPart(f"bearing unit {label}", unit, "dark_steel", "static"))
        for dy in (-1, 1):
            for dz in (-1, 1):
                c = (lay["bearing_od"] + 24) / 2 - 8
                bx = x_out + 6 if s > 0 else x_out - 10  # bolt heads on the outer face
                parts.append(VPart(f"bearing bolt {label} {dy} {dz}",
                                   _hex_bolt(cq, bx, dy * c, axis_z + dz * c, 7, 4, "X"), "steel", "static"))
    sx, sy = st.bolt_spacing_mm
    yc = (base_bb.ymin + base_bb.ymax) / 2
    for bx in (-sx / 2, sx / 2):
        for by in (-sy / 2, sy / 2):
            parts.append(VPart(f"anchor bolt {bx:.0f} {by:.0f}", _hex_bolt(cq, bx, yc + by, base_bb.zmax, 10, 6),
                               "steel", "static"))

    # --- enclosure proposal (fits around the mechanism with clearance)
    xs = base_bb.xmax + 12
    y0, y1 = base_bb.ymin - 12, base_bb.ymax + 12
    top = axis_z + max(flange_r, wheel_pd / 2, motor_d / 2) + 18
    radius = 22.0
    outer = (cq.Workplane("XY").box(2 * xs, y1 - y0, top + 4, centered=(True, False, False))
             .translate((0, y0, -4)).edges().fillet(radius))
    inner = (cq.Workplane("XY").box(2 * xs - 6, y1 - y0 - 6, top - 2, centered=(True, False, False))
             .translate((0, y0 + 3, -1)).edges().fillet(radius - 3))  # closed 3 mm wall all round
    shell = outer.cut(inner)
    split_z = base_bb.zmax + 30  # tray below, translucent cover above
    tray = shell.intersect(cq.Workplane("XY").box(4 * xs, 4 * (y1 - y0), split_z + 4, centered=(True, True, False))
                           .translate((0, 0, -4)))
    cover = shell.cut(cq.Workplane("XY").box(4 * xs, 4 * (y1 - y0), split_z + 4, centered=(True, True, False))
                      .translate((0, 0, -4)))
    exit_z = axis_z + core_r
    port = cq.Workplane("XZ").workplane(offset=-(y1 + 1)).center(0, exit_z).circle(26).extrude(10)
    fascia_cut = cq.Workplane("XY").box(2 * xs + 2, 16, top + 10, centered=(True, False, False)).translate((0, y1 - 13, -5))
    fascia = shell.intersect(fascia_cut).cut(port)
    cover = cover.cut(fascia_cut).cut(port)
    tray = tray.cut(fascia_cut).cut(port)
    for s in (-1, 1):  # side vent slots
        vents = (cq.Workplane("YZ").workplane(offset=s * xs - 10).center((y0 + y1) / 2, split_z * 0.55)
                 .rarray(14, 1, 7, 1).slot2D(5, 26, 90).extrude(20))
        tray = tray.cut(vents)
    parts.append(VPart("enclosure tray", tray, "graphite", "static"))
    parts.append(VPart("enclosure cover", cover, "glass", "static"))
    parts.append(VPart("enclosure fascia", fascia, "fascia", "static"))
    bell = (cq.Workplane("XZ").workplane(offset=-(y1 + 2)).center(0, exit_z).circle(30).circle(9).extrude(14)
            .edges().fillet(2.0))
    parts.append(VPart("cable port bellmouth", bell, "alu", "static"))
    # arrestor cone: revolved hollow frustum (rubber), wide end at the fascia
    cone = (cq.Workplane("XY").polyline([(9, 0), (22, 0), (22, 3), (12, 26), (9, 26)]).close()
            .revolve(360, (0, 0, 0), (0, 1, 0)).translate((0, y1 + 16, exit_z)))
    parts.append(VPart("arrestor cone", cone, "rubber", "static"))
    light = (cq.Workplane("XY").box(2 * xs * 0.55, 2.5, 2.5).edges("|X").fillet(1.0)
             .translate((0, y1 + 0.4, top - 18)))
    parts.append(VPart("status light", light, "light", "static"))
    port_point = (0.0, y1 + 42, exit_z)  # where the cable leaves the arrestor cone
    pivots = {"drum": (0.0, 0.0, axis_z), "motor_left": (0.0, y_motor, axis_z), "motor_right": (0.0, y_motor, axis_z)}
    info = {"wrap": wrap_spec, "port_point_mm": port_point, "drum_radius_mm": core_r + d_cable / 2, "ratio": opt.external_ratio,
            "enclosure_mm": (2 * xs, y1 - y0, top + 4), "back_y_mm": y0, "floor_z_mm": -4.0}
    return parts, pivots, info


def r_out_wheel(st):
    return st.wheel_teeth * st.belt_pitch_mm / (2 * math.pi) - 0.57


def handle(cq_unused=None):
    """Straight bar with rubber grips, centre swivel eye. Built along X, centred, mm; eye points -Y."""
    cq = cad._cq()
    bar = cq.Workplane("YZ").workplane(offset=-250).circle(14).extrude(500).faces("<X or >X").chamfer(2.0)
    grips = [cq.Workplane("YZ").workplane(offset=s * 170 - 50).circle(16.5).extrude(100).edges().fillet(3.0)
             for s in (-1, 1)]
    caps = [cq.Workplane("YZ").workplane(offset=s * 250 - (0 if s > 0 else 8)).circle(17).extrude(8)
            .edges().fillet(2.5) for s in (-1, 1)]
    swivel = cq.Workplane("XZ").circle(10).extrude(-30).translate((0, -14, 0)).edges().fillet(2.0)
    ring = (cq.Workplane("XZ").workplane(offset=44).circle(14).circle(9).extrude(5)
            .rotate((0, 0, 0), (0, 0, 1), 90).translate((0, 0, 0)))
    parts = [VPart("bar", bar, "steel", "handle"), VPart("swivel", swivel, "dark_steel", "handle"),
             VPart("eye", ring.translate((0, -48, 0)), "dark_steel", "handle")]
    parts += [VPart(f"grip {i}", g, "rubber", "handle") for i, g in enumerate(grips)]
    parts += [VPart(f"cap {i}", c, "rubber", "handle") for i, c in enumerate(caps)]
    return parts


def tessellate(shape, pivot_mm=(0.0, 0.0, 0.0), tol=0.15, ang=0.15):
    """Per-face tessellation with smooth normals inside each face and crisp edges between faces.

    Returns positions (metres, glTF Y-up, relative to the pivot), normals, indices.
    """
    pos, nrm, idx = [], [], []
    base = 0
    px, py, pz = pivot_mm
    for face in shape.val().Faces():
        verts, tris = face.tessellate(tol, ang)
        if not tris:
            continue
        v = np.array([(p.x - px, p.y - py, p.z - pz) for p in verts], dtype=float)
        t = np.array(tris, dtype=np.int64)
        fn = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
        vn = np.zeros_like(v)
        for k in range(3):
            np.add.at(vn, t[:, k], fn)
        lens = np.linalg.norm(vn, axis=1, keepdims=True)
        vn = np.where(lens > 0, vn / np.maximum(lens, 1e-30), np.array([0.0, 0.0, 1.0]))
        pos.append(v)
        nrm.append(vn)
        idx.append(t + base)
        base += len(v)
    if not pos:
        return None
    p = np.concatenate(pos) / 1000.0
    n = np.concatenate(nrm)
    to_y_up = lambda a: np.stack([a[:, 0], a[:, 2], -a[:, 1]], axis=1)  # noqa: E731  (x, y, z) -> (x, z, -y)
    return to_y_up(p).astype(np.float32), to_y_up(n).astype(np.float32), np.concatenate(idx).ravel().astype(np.uint32)


def mm_to_gltf(p):
    x, y, z = p
    return (x / 1000.0, z / 1000.0, -y / 1000.0)


def wrap_mesh(spec, sides=10, seg_per_turn=40):
    """Helical cable tube about the X axis (relative to the drum pivot), glTF metres Y-up."""
    n = spec["turns"] * seg_per_turn + 1
    th = np.linspace(0, 2 * np.pi * spec["turns"], n)
    x = spec["x0"] + spec["pitch"] * th / (2 * np.pi)
    centre = np.stack([x, spec["radius"] * np.cos(th), spec["radius"] * np.sin(th)], axis=1)
    tangent = np.gradient(centre, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1, keepdims=True)
    radial = np.stack([np.zeros(n), np.cos(th), np.sin(th)], axis=1)
    b = np.cross(tangent, radial)
    phi = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    ring = np.cos(phi)[None, :, None] * radial[:, None, :] + np.sin(phi)[None, :, None] * b[:, None, :]
    pos = (centre[:, None, :] + spec["tube_r"] * ring).reshape(-1, 3)
    nrm = ring.reshape(-1, 3)
    i, j = np.meshgrid(np.arange(n - 1), np.arange(sides), indexing="ij")
    a = i * sides + j
    b2 = i * sides + (j + 1) % sides
    c = (i + 1) * sides + j
    d = (i + 1) * sides + (j + 1) % sides
    idx = np.stack([a, c, b2, b2, c, d], axis=-1).reshape(-1)
    to_y_up = lambda v: np.stack([v[:, 0], v[:, 2], -v[:, 1]], axis=1)  # noqa: E731
    return (to_y_up(pos / 1000.0).astype(np.float32), to_y_up(nrm).astype(np.float32), idx.astype(np.uint32))
