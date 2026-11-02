"""Electronics packaging inside the floor platform (first pass, A-024).

Places the electrical parts in the free space between the mechanism and the sheave
cross-beam, under the deck and clear of the rope's path. It routes the main cables
as swept tubes and adds vents, an exhaust fan, the mains inlet, an e-stop and the
deck presence pads. Everything is checked for interference against the mechanism,
the platform and a rope keep-out zone. Device frame, mm: X across, Y forward, Z up.
"""
from __future__ import annotations

from dataclasses import dataclass

from odrt import cad


@dataclass
class PPart:
    name: str
    shape: object
    material: str      # key into visual.MATERIALS (or "none")
    kind: str          # "electronics", "cable", "keepout", "platform"


def _box(cq, name, dims, corner, material, kind="electronics", fillet=2.0):
    lx, ly, lz = dims
    b = cq.Workplane("XY").box(lx, ly, lz, centered=False).translate(corner)
    if fillet:
        try:
            b = b.edges("|Z").fillet(min(fillet, lx / 3, ly / 3))
        except Exception:  # noqa: BLE001  (tiny parts: keep sharp edges)
            pass
    return PPart(name, b, material, kind)


def _cable(cq, name, points, diameter, material):
    """Round tube swept along a polyline with rounded corners."""
    path = cq.Workplane("XY").polyline(points)
    x0, y0, z0 = points[0]
    x1, y1, z1 = points[1]
    import math
    d = (x1 - x0, y1 - y0, z1 - z0)
    n = math.sqrt(sum(v * v for v in d))
    plane = cq.Plane(origin=(x0, y0, z0), xDir=_perp(d), normal=tuple(v / n for v in d))
    prof = cq.Workplane(plane).circle(diameter / 2)
    tube = prof.sweep(path, transition="round")
    return PPart(name, tube, material, "cable")


def _perp(d):
    import numpy as np
    d = np.array(d, dtype=float)
    a = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 * np.linalg.norm(d) else np.array([1.0, 0, 0])
    p = np.cross(d, a)
    return tuple(p / np.linalg.norm(p))


def build(st, opt, common, sizes, cfg_platform, z, el_parts, swivel_cfg=None):
    cq = cad._cq()
    plat_parts, geo = cad.build_platform(st, opt, common, sizes, cfg_platform, z)
    plat_parts = list(plat_parts)
    lay = cad.layout(st, opt, common, sizes)
    exit_z = geo["cable_exit_height_mm"]
    width = z["platform_width_mm"]
    xs_in = width / 2 - 6                    # inside face of the skirts
    y_port = geo["port_y_mm"]
    yc, zc = geo["sheave_centre_mm"]
    deck_under = cfg_platform.deck_h_mm - cfg_platform.deck_t_mm
    bw, bh, _ = cfg_platform.stringer_section_mm
    beam_y = yc - cfg_platform.sheave_r_mm - bw / 2 - 5
    mech_front = max(p.shape.val().BoundingBox().ymax for p in plat_parts
                     if p.name.startswith(("fairlead", "base plate", "side plate", "motor")))
    y0, y1 = mech_front + 15, beam_y - bw / 2 - 10           # free bay between mechanism and cross-beam
    parts = []

    # rope keep-out: drum top to sheave, +-45 mm for the fleet angle, +-15 mm vertically
    parts.append(PPart("rope keep-out", cq.Workplane("XY").box(90, yc - 0, 30, centered=(True, False, True))
                       .translate((0, 0, exit_z)), "none", "keepout"))

    d = {k: v.dims_mm for k, v in el_parts.items()}
    # power supply lying flat on the right, under the rope band
    psu_l, psu_w, psu_h = d["psu"]
    psu_x0 = xs_in - psu_l - 35  # leave a 30 mm service gap at the skirt for the mains cable
    parts.append(_box(cq, "power supply (RSP-1000-48)", (psu_l, psu_w, psu_h), (psu_x0, y0, 0), "psu"))
    # supercapacitor bank: large cells standing, 3 rows, on the left
    cl, _, ch = d["cap_cell_large"]
    n_cells = el_parts["cap_cell_large"].qty
    per_row = 8
    bank_x0 = -xs_in + 8
    for i in range(n_cells):
        row, col = divmod(i, per_row)
        cx = bank_x0 + cl / 2 + col * (cl + 1)
        cy = y0 + cl / 2 + row * (cl + 1)
        cell = cq.Workplane("XY").circle(cl / 2).extrude(ch).translate((cx, cy, 4)).edges(">Z").fillet(2.0)
        parts.append(PPart(f"buffer cell {i + 1}", cell, "cap", "electronics"))
    bank_y1 = y0 + 3 * (cl + 1)
    parts.append(_box(cq, "buffer tray + balancing board", (per_row * (cl + 1) + 6, bank_y1 - y0 + 6, 4),
                      (bank_x0 - 3, y0 - 3, 0), "pcb", fillet=0))
    # drive + heatsink + fan stack, behind the bank on the left
    dl, dw, dh = d["drive_heatsink"]
    drive_x = -xs_in + 20
    drive_y = bank_y1 + 12
    parts.append(_box(cq, "drive heat spreader + heatsink", (dl, dw, dh), (drive_x, drive_y, 0), "alu"))
    ol, ow, oh = d["drive"]
    parts.append(_box(cq, "motor drive (ODrive S1)", (ol, ow, oh / 2), (drive_x + (dl - ol) / 2, drive_y + (dw - ow) / 2, dh),
                      "pcb", fillet=0))
    fan_d = 60
    parts.append(PPart("drive fan (60 mm)", cq.Workplane("XY").rect(fan_d, fan_d).extrude(15)
                       .cut(cq.Workplane("XY").circle(fan_d / 2 - 3).extrude(15))
                       .translate((drive_x + dl + 2 + fan_d / 2, drive_y + dw / 2, 0)), "fan", "electronics"))
    # safety controller and STO relay on the right, behind the supply
    sl, sw, sh = d["safety_mcu"]
    parts.append(_box(cq, "independent safety controller", (sl, sw, sh), (xs_in - sl - 10, y0 + psu_w + 15, 0), "pcb"))
    rl, rw, rh = d["sto_relay"]
    parts.append(_box(cq, "STO / power-loss braking relay", (rl, rw, rh), (xs_in - sl - rl - 25, y0 + psu_w + 15, 0),
                      "relay"))
    # braking resistor on top of the supply, next to the exhaust fan (its heat leaves directly)
    bl, bw2, bh2 = d["brake_resistor"]
    parts.append(_box(cq, "braking resistor 0.5 ohm", (bl, bw2, bh2), (psu_x0 + psu_l - bl - 30, y0 + 10, psu_h + 4),
                      "alu"))
    # exhaust fan on the right skirt above the supply; intake vent slots on the left skirt
    fan = d["fan"][0]
    fy = y0 + psu_w / 2
    fan_z0 = psu_h + 8
    parts.append(PPart("exhaust fan (80 mm)", cq.Workplane("YZ").rect(fan, fan).extrude(-25)
                       .cut(cq.Workplane("YZ").circle(fan / 2 - 3).extrude(-25))
                       .translate((xs_in, fy, fan_z0 + fan / 2)), "fan", "electronics"))
    # mains inlet module on the right skirt near the back, e-stop on the deck's back-right corner
    ml, mw, mh = d["mains_inlet"]
    y_back = geo["platform_y_back_mm"]
    parts.append(_box(cq, "mains inlet + switch + fuse", (mh, ml, mw), (xs_in - mh, y_back + 60, 30), "black", fillet=1))
    el, ew, eh = d["estop"]
    estop = (cq.Workplane("XY").circle(el / 2).extrude(eh * 0.4).faces(">Z").workplane().circle(el / 2 + 6)
             .extrude(eh * 0.3).translate((width / 2 - 45, y_back + 45, cfg_platform.deck_h_mm)))
    parts.append(PPart("emergency stop", estop, "estop", "electronics"))
    # presence pads between the deck and the stringers, under each foot (front and back of the port)
    pl, pw, ph = d["presence_pad"]
    for sx in (-1, 1):
        for dy in (-90, 90):
            parts.append(_box(cq, f"presence pad {sx:+d}{dy:+d}", (pl, pw, ph),
                              (sx * cfg_platform.stance_half_mm - pl / 2, y_port + dy - pw / 2, deck_under - ph), "black",
                              fillet=0))

    # cables (diameters include insulation; gauges from the electronics budget). Power cables run in a
    # tray level above the capacitor bank and below the rope band; nothing crosses the rope keep-out.
    tray_z = 6 + ch + 12
    motor_parts = [p for p in plat_parts if p.name.startswith("motor ")]
    mb = motor_parts[0].shape.val().BoundingBox()
    mot_y, mot_z = (mb.ymin + mb.ymax) / 2, (mb.zmin + mb.zmax) / 2
    drv_top = (drive_x + 10, drive_y + dw / 2, dh + oh / 2 + 4)
    route_x = -xs_in + 14
    phase = [drv_top, (drive_x + 10, drive_y + dw / 2, tray_z), (route_x, drive_y + dw / 2, tray_z),
             (route_x, mot_y, tray_z), (route_x, mot_y, mot_z), (mb.xmin - 4, mot_y, mot_z)]
    parts.append(_cable(cq, "motor phase cable (3 x AWG 8)", phase, 14, "cable_orange"))
    # DC bus goes around the buffer bank (behind it), never over the capacitor terminals
    psu_top = (psu_x0 + 25, y0 + psu_w / 2, psu_h + 5)
    behind_bank = drive_y + dw / 2
    bus = [psu_top, (psu_x0 + 25, y0 + psu_w / 2, 52), (psu_x0 + 25, behind_bank, 52),
           (drive_x + dl - 10, behind_bank, 52), (drive_x + dl - 10, behind_bank, dh + oh / 2 + 4)]
    parts.append(_cable(cq, "DC bus cable (2 x AWG 8)", bus, 10, "cable_red"))
    inlet = (xs_in - mh - 4, y_back + 60 + ml / 2, 30 + mw / 2)
    # runs low along the skirt (under the exhaust fan), then up the service gap into the supply's input end
    mains = [inlet, (xs_in - 18, y_back + 60 + ml / 2, 30 + mw / 2), (xs_in - 18, y_back + 60 + ml / 2, 18),
             (xs_in - 18, y0 + psu_w - 15, 18), (xs_in - 18, y0 + psu_w - 15, psu_h + 6),
             (psu_x0 + psu_l - 10, y0 + psu_w - 15, psu_h + 6)]
    parts.append(_cable(cq, "mains cable (3 x 1.5 mm2)", mains, 8, "cable_black"))
    pin = (cfg_platform.sheave["cheek_gap_mm"] / 2 + cfg_platform.sheave["cheek_thickness_mm"] + 3, yc, zc)
    sig_end = (xs_in - sl - 10 + sl / 2, y0 + psu_w + 15 + sw + 4, sh / 2)
    signal = [pin, (75, yc, zc), (75, yc, 12), (75, sig_end[1] + 20, 12), (sig_end[0], sig_end[1] + 20, 12),
              (sig_end[0], sig_end[1], 12)]
    parts.append(_cable(cq, "load-pin signal cable", signal, 5, "cable_black"))
    if swivel_cfg is not None:
        parts += swivel_head(cq, swivel_cfg, cfg_platform, y_port)
    # vent slots in the left skirt (intake, low) and the fan opening in the right skirt (exhaust)
    for i, p in enumerate(plat_parts):
        if p.name == "skirt left":
            slots = (cq.Workplane("YZ").workplane(offset=-width / 2 - 5).center((y0 + y1) / 2, 45)
                     .rarray(16, 1, 12, 1).slot2D(60, 6, 90).extrude(20))
            plat_parts[i] = cad.Part(p.name, p.shape.cut(slots), p.material, p.moving)
        elif p.name == "skirt right":
            hole = (cq.Workplane("YZ").workplane(offset=width / 2 - 10).center(fy, fan_z0 + fan / 2)
                    .circle(fan / 2 - 3).extrude(20))
            plat_parts[i] = cad.Part(p.name, p.shape.cut(hole), p.material, p.moving)
    return plat_parts, parts, geo, (y0, y1)


def swivel_head(cq, sw, cfg_platform, y_port):
    """Swivel exit on the deck: bearing housing in the deck, rotating head with exit sheave, guard dome.
    Shown with the exit plane facing forward (+Y) at zero tilt."""
    deck_top = cfg_platform.deck_h_mm
    r_house = cfg_platform.port_radius_mm - 1
    parts = []
    # flush with the deck underside (the under-deck sheave cheeks end there) and 6 mm proud of the deck top
    housing = (cq.Workplane("XY").circle(r_house).circle(sw.bearing_pcd_mm / 2 - 8).extrude(cfg_platform.deck_t_mm + 5)
               .translate((0, y_port, deck_top - cfg_platform.deck_t_mm + 0.5)))
    parts.append(PPart("swivel bearing housing", housing, "alu", "electronics"))
    base_z = deck_top + 6
    plate = cq.Workplane("XY").circle(sw.bearing_pcd_mm / 2 + 6).circle(9).extrude(6).translate((0, y_port, base_z))
    parts.append(PPart("swivel head plate", plate, "dark_steel", "electronics"))
    r = sw.sheave_r_mm
    zc = base_z + sw.head_h_mm
    yc = y_port + r  # vertical rope leg is tangent to the sheave on the swivel axis
    for s in (-1, 1):
        cheek = (cq.Workplane("XY").box(5, 2 * r + 24, zc + 12 - (base_z + 6), centered=(True, True, False))
                 .translate((s * 12, yc - 6, base_z + 6)))
        parts.append(PPart(f"swivel cheek {'left' if s < 0 else 'right'}", cheek, "alu", "electronics"))
    sheave = cq.Workplane("YZ").workplane(offset=-7).center(yc, zc).circle(r).circle(6).extrude(14)
    groove = cq.Workplane("YZ").workplane(offset=-1.5).center(yc, zc).circle(r + 0.1).circle(r - 2.2).extrude(3)
    parts.append(PPart("swivel exit sheave", sheave.cut(groove), "steel", "electronics"))
    axle = cq.Workplane("YZ").workplane(offset=-17).center(yc, zc).circle(6).extrude(34)
    parts.append(PPart("swivel exit axle", axle, "steel", "electronics"))
    dome_r = sw.dome_r_mm
    dome = (cq.Workplane("XY").sphere(dome_r).cut(cq.Workplane("XY").sphere(dome_r - 3))
            .cut(cq.Workplane("XY").box(4 * dome_r, 4 * dome_r, 2 * dome_r).translate((0, 0, -dome_r)))
            .translate((0, y_port, base_z)))
    # rope slot through the dome: vertical over the axis, sweeping forward to near-horizontal (max tilt)
    slot = (cq.Workplane("YZ").workplane(offset=-10).center(0, 0)
            .polyline([(-6, 0), (-6, dome_r + 5), (dome_r + 5, dome_r + 5), (dome_r + 5, 6), (6, 6)]).close()
            .extrude(20).translate((0, y_port, base_z + 2)))
    parts.append(PPart("swivel guard dome", dome.cut(slot), "graphite", "electronics"))
    return parts


PLATFORM_MATERIALS = {"platform pan": "dark_steel", "stringer": "dark_steel", "end frame": "dark_steel",
                      "sheave cross-beam": "dark_steel", "skirt": "graphite", "deck": "deck_mat",
                      "turning sheave": "alu", "sheave cheek": "alu", "sheave axle": "steel", "rubber foot": "rubber"}
MECH_ONLY = ("enclosure", "cable port", "arrestor", "status light")


EXPLODE = (  # (name prefix, offset mm in device frame); first match wins
    ("deck", (0, 0, 330)), ("presence pad", (0, 0, 270)), ("emergency stop", (0, 0, 330)),
    ("swivel guard dome", (0, 0, 520)), ("swivel exit", (0, 0, 450)), ("swivel cheek", (0, 0, 450)),
    ("swivel head plate", (0, 0, 420)), ("swivel bearing housing", (0, 0, 390)),
    ("stringer", (0, 0, 200)), ("sheave cross-beam", (0, 120, 200)),
    ("skirt left", (-220, 0, 0)), ("skirt right", (220, 0, 0)), ("end frame back", (0, -220, 0)),
    ("end frame front", (0, 220, 0)), ("rubber foot", (0, 0, -60)),
    ("turning sheave", (0, 160, 60)), ("sheave cheek left", (-40, 160, 60)), ("sheave cheek right", (40, 160, 60)),
    ("sheave axle", (0, 160, 60)),
    ("motor can", (-170, 0, 40)), ("motor stator", (-130, 0, 40)), ("motor shaft", (-110, 0, 40)),
    ("pinion", (-90, 0, 40)), ("belt", (-70, 0, 70)), ("wheel", (-50, 0, 0)), ("motor bracket", (-140, 0, 0)),
    ("bearing unit left", (-30, 0, 0)), ("bearing unit right", (30, 0, 0)), ("bearing bolt left", (-45, 0, 0)),
    ("bearing bolt right", (45, 0, 0)), ("side plate left", (-15, 0, 0)), ("side plate right", (15, 0, 0)),
    ("shaft", (0, 0, 90)), ("drum", (0, 0, 60)), ("cable wrap", (0, 0, 60)),
    ("buffer cell", (0, 0, 140)), ("buffer tray", (0, 0, 90)),
    ("motor drive", (0, 0, 170)), ("drive fan", (0, 0, 120)), ("drive heat", (0, 0, 120)),
    ("braking resistor", (0, 0, 190)), ("power supply", (0, 0, 120)), ("independent safety", (0, 0, 120)),
    ("STO", (0, 0, 120)), ("exhaust fan", (120, 0, 0)), ("mains inlet", (120, 0, 0)),
    ("motor phase cable", (0, 0, 90)), ("DC bus cable", (0, 0, 100)), ("mains cable", (60, 0, 0)),
    ("load-pin signal cable", (0, 60, 40)),
)


def explode_offset(name):
    return next((off for prefix, off in EXPLODE if name.startswith(prefix)), (0, 0, 0))


def export_glb(vis_parts, pivots, info, plat_parts, parts, geo, path, cutaway=False, rope=True, exploded=False):
    """Static GLB of the packaged platform (visual model + platform + electronics), metres, Y up."""
    import dataclasses

    import numpy as np

    from odrt import visual
    from odrt.gltf import Mesh, Node, Scene, quat_between
    scene = Scene()
    for key, m in visual.MATERIALS.items():
        scene.material(dataclasses.replace(m, name=key))
    root = scene.node(Node("odrt500_platform"))

    def add(name, shape, material, pivot=(0.0, 0.0, 0.0)):
        mesh = visual.tessellate(shape, pivot)
        if mesh is None:
            return
        off = explode_offset(name) if exploded else (0, 0, 0)
        scene.mesh(Mesh(name, *mesh, material))
        scene.node(Node(name, mesh=name, translation=visual.mm_to_gltf(tuple(p + o for p, o in zip(pivot, off)))),
                   root.name)

    for p in vis_parts:
        if p.name.startswith(MECH_ONLY):
            continue
        add(p.name, p.shape, p.material, pivots.get(p.group, (0.0, 0.0, 0.0)))
    wrap = visual.wrap_mesh(info["wrap"])
    scene.mesh(Mesh("cable wrap", *wrap, "rope"))
    wrap_at = tuple(p + o for p, o in zip(pivots["drum"], explode_offset("cable wrap") if exploded else (0, 0, 0)))
    scene.node(Node("cable wrap", mesh="cable wrap", translation=visual.mm_to_gltf(wrap_at)), root.name)
    for p in plat_parts:
        mat = next((v for k, v in PLATFORM_MATERIALS.items() if p.name.startswith(k)), None)
        if mat is None:
            continue  # mechanism parts already come from the visual model
        if cutaway and (p.name in ("deck", "skirt right") or p.name.startswith("presence pad")):
            continue
        add(p.name, p.shape, mat)
    for p in parts:
        if p.kind == "keepout":
            continue
        add(p.name, p.shape, p.material)
    if rope and not exploded:  # rope from the drum to the sheave, then up through the deck port
        yc, zc = geo["sheave_centre_mm"]
        r = (yc - geo["port_y_mm"]) * -1
        exit_pt = np.array(visual.mm_to_gltf((0.0, pivots["drum"][1], geo["cable_exit_height_mm"])))
        bottom = np.array(visual.mm_to_gltf((0.0, yc, zc - r)))
        top0 = np.array(visual.mm_to_gltf((0.0, geo["port_y_mm"], zc)))
        top1 = np.array(visual.mm_to_gltf((0.0, geo["port_y_mm"], 260.0)))
        from odrt.animate import _cylinder
        cyl = _cylinder(0.0019, 16)
        scene.mesh(Mesh("rope", *cyl, "rope"))
        for i, (a, b) in enumerate(((exit_pt, bottom), (top0, top1))):
            d = b - a
            scene.node(Node(f"rope {i}", mesh="rope", translation=tuple(a),
                            rotation=tuple(quat_between([0, 1.0, 0], d[None, :])[0]),
                            scale=(1.0, float(np.linalg.norm(d)), 1.0)), root.name)
    path.write_bytes(scene.to_glb())
    return path


ALLOWED = {  # intended contacts: (prefix A, prefix B)
    ("rope keep-out", "cable layers"), ("rope keep-out", "fairlead"), ("rope keep-out", "turning sheave"),
    ("rope keep-out", "sheave cheek"), ("rope keep-out", "drum"), ("rope keep-out", "sheave axle"),
    ("presence pad", "stringer"), ("presence pad", "deck"),
    ("motor phase cable", "motor drive"), ("motor phase cable", "motor left"), ("motor phase cable", "motor right"),
    ("DC bus cable", "power supply"), ("DC bus cable", "motor drive"), ("DC bus cable", "drive heat"),
    ("mains cable", "mains inlet"), ("mains cable", "power supply"), ("mains cable", "skirt"),
    ("load-pin signal cable", "sheave"), ("load-pin signal cable", "independent safety"),
    ("swivel bearing housing", "deck"), ("swivel head plate", "swivel cheek"), ("swivel cheek", "swivel exit axle"),
    ("swivel exit sheave", "swivel exit axle"), ("swivel guard dome", "swivel head plate"),
    ("rope keep-out", "swivel"),
    ("buffer cell", "buffer tray"), ("motor drive", "drive heat"), ("braking resistor", "power supply"),
    ("exhaust fan", "skirt"), ("mains inlet", "skirt"), ("emergency stop", "deck"),
    ("power supply", "platform pan"), ("buffer tray", "platform pan"), ("drive heat", "platform pan"),
    ("drive fan", "platform pan"), ("independent safety", "platform pan"), ("STO", "platform pan"),
}


def interferences(plat_parts, parts, tol=1.0):
    """Clashes between a new part (electronics, cables, keep-out) and anything else, minus intended contacts."""
    names_new = {p.name for p in parts}
    allp = [(p.name, p.shape.val()) for p in plat_parts] + [(p.name, p.shape.val()) for p in parts]

    def ok(a, b):
        return any((a.startswith(x) and b.startswith(y)) or (a.startswith(y) and b.startswith(x)) for x, y in ALLOWED)

    out = []
    for i in range(len(allp)):
        for j in range(i + 1, len(allp)):
            (na, sa), (nb, sb) = allp[i], allp[j]
            if na not in names_new and nb not in names_new:
                continue
            if ok(na, nb):
                continue
            A, B = sa.BoundingBox(), sb.BoundingBox()
            if (A.xmax < B.xmin or B.xmax < A.xmin or A.ymax < B.ymin or B.ymax < A.ymin
                    or A.zmax < B.zmin or B.zmax < A.zmin):
                continue
            v = sa.intersect(sb).Volume()
            if v > tol:
                out.append((na, nb, v))
    return out
    return plat_parts, parts, geo, (y0, y1)
