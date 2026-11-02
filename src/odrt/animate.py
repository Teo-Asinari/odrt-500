"""Exercise animations: mannequin + device + cable + handle as animated GLB scenes.

The human motion is keyframed (mannequin.py) and timed by the scenario's motion
profile (same min-jerk timing as WP1). The device responds to the resulting
handle path: cable payout = distance from the cable port to the bar, the drum
turns by payout / radius, and the motors turn `ratio` times faster through the
belts. Kinematics only: no forces are shown.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from odrt import mannequin as mq
from odrt import visual
from odrt.gltf import Channel, Mesh, Node, Scene, quat_axis_angle, quat_between, quat_mul, quat_rotate
from odrt.scenarios import PHASE_REST, generate

FPS = 30


@dataclass(frozen=True)
class Exercise:
    name: str
    scenario: str
    reps: int
    start: dict              # pose at the bottom of the stroke (cable least extended)
    end: dict                # pose at the top of the stroke
    human_z: float           # mannequin ankle depth in front of the wall (m), facing the wall
    mount: str               # "wall_bracket" or "floor_wall"
    port_height: float = 0.0 # cable port height for the wall bracket (m)
    redirect: bool = False   # floor pulley under the bar turns the cable upward


LEGS_SOFT = {"pelvis_lean": 6.0, "torso_lean": 8.0, "thigh_fwd": 10.0, "shin_fwd": -8.0}
EXERCISES = (
    Exercise("row", "row_reference", 3,
             start={**LEGS_SOFT, "upper_arm_fwd": 72.0, "forearm_fwd": 78.0},
             end={**LEGS_SOFT, "upper_arm_fwd": -28.0, "forearm_fwd": 62.0},
             human_z=1.55, mount="wall_bracket", port_height=1.15),
    Exercise("curl", "curl_reference", 3,
             start={"pelvis_lean": 0.0, "torso_lean": 2.0, "thigh_fwd": 2.0, "shin_fwd": -2.0,
                    "upper_arm_fwd": 6.0, "forearm_fwd": 12.0},
             end={"pelvis_lean": 0.0, "torso_lean": -2.0, "thigh_fwd": 2.0, "shin_fwd": -2.0,
                  "upper_arm_fwd": 12.0, "forearm_fwd": 140.0},
             human_z=0.55, mount="floor_wall"),
    Exercise("deadlift", "heavy_tempo_limit", 2,
             start={"pelvis_lean": 48.0, "torso_lean": 52.0, "thigh_fwd": 58.0, "shin_fwd": -18.0,
                    "upper_arm_fwd": 0.0, "forearm_fwd": 0.0},
             end={"pelvis_lean": 0.0, "torso_lean": 0.0, "thigh_fwd": 1.0, "shin_fwd": -1.0,
                  "upper_arm_fwd": 0.0, "forearm_fwd": 0.0},
             human_z=1.25, mount="floor_wall", redirect=True),
)


def progress_curve(inputs, ex: Exercise):
    """Time base and 0..1 movement progress from the scenario's own motion profile."""
    s = inputs.scenarios[ex.scenario]
    traj = generate(s, inputs.defaults)
    t_end = 1.0 + inputs.defaults.tension_ramp_s + ex.reps * s.cycle_s() + 0.6
    t = np.arange(0.0, t_end, 1.0 / FPS)
    x = np.interp(t, traj.t, traj.x)
    u = np.clip((x - s.start_offset_m) / s.stroke_m, 0.0, 1.0)
    return t, u


def _device_root_transform(mount: str, info: dict, port_target=None):
    """(translation, rotation) of the device root in world glTF metres."""
    back = -info["back_y_mm"] / 1000.0  # device-frame distance from origin to the enclosure back
    rot = quat_axis_angle([0, 1.0, 0], np.pi)  # cable exits toward +Z, away from the wall at z = 0
    port_local = np.array(visual.mm_to_gltf(info["port_point_mm"]))
    height = 0.0 if mount == "floor_wall" else port_target - port_local[1]
    return np.array([0.0, height - info["floor_z_mm"] / 1000.0, back]), rot


def build_scene(inputs, parts, pivots, info, handle_parts, ex: Exercise = None) -> tuple:
    scene = Scene()
    import dataclasses
    for key, m in visual.MATERIALS.items():  # meshes refer to materials by key
        scene.material(dataclasses.replace(m, name=key))
    report = {}

    # environment
    floor = visual.mm_to_gltf  # noqa: F841 (kept for symmetry with device helpers)
    from odrt.mannequin import ellipsoid  # noqa: F401
    _box(scene, "floor", (4.0, 0.02, 4.0), (0, -0.01, 1.0), "floor")
    _box(scene, "wall", (4.0, 2.6, 0.02), (0, 1.3, -0.01), "wall")

    # timing and human motion
    if ex is not None:
        t, u = progress_curve(inputs, ex)
        poses = mq.interpolate(ex.start, ex.end, u)
        joints = {k: [mq.fk({kk: poses[kk][i] for kk in mq.POSE_KEYS}) for i in range(len(t))] for k in [0]}[0]
        ground = np.array([mq.grounded_pelvis({kk: poses[kk][i] for kk in mq.POSE_KEYS}) for i in range(len(t))])
        grip_local = np.array([j["grip"] for j in joints]) + ground  # mannequin frame
        yaw = quat_axis_angle([0, 1.0, 0], np.pi)  # face the wall
        human_pos = np.array([0.0, 0.0, ex.human_z])
        grip_world = quat_rotate(yaw, grip_local) + human_pos
    # device
    if ex is None:
        tr, rot = _device_root_transform("floor_wall", info)
    else:
        tr, rot = _device_root_transform(ex.mount, info, port_target=ex.port_height)
    root = scene.node(Node("device", translation=tuple(tr), rotation=tuple(rot)))
    groups = {"static": root.name}
    for g, pv in pivots.items():
        scene.node(Node(g, translation=visual.mm_to_gltf(pv)), root.name)
        groups[g] = g
    for p in parts:
        pv = pivots.get(p.group, (0.0, 0.0, 0.0))
        mesh = visual.tessellate(p.shape, pv)
        if mesh is None:
            continue
        scene.mesh(Mesh(p.name, *mesh, p.material))
        scene.node(Node(f"{p.name} node", mesh=p.name), groups[p.group])
    wrap = visual.wrap_mesh(info["wrap"])
    scene.mesh(Mesh("cable wrap", *wrap, "rope"))
    scene.node(Node("cable wrap node", mesh="cable wrap"), "drum")
    if ex is not None and ex.mount == "wall_bracket":
        shelf_y = tr[1] - 0.006
        _box(scene, "wall bracket", (0.36, 0.012, 0.34), (0, shelf_y, 0.17), "graphite")

    # handle and cable
    port_world = quat_rotate(rot, np.array(visual.mm_to_gltf(info["port_point_mm"]))) + tr
    h = scene.node(Node("handle"))
    for p in handle_parts:
        mesh = visual.tessellate(p.shape, (0.0, 0.0, 0.0))
        scene.mesh(Mesh(p.name, *mesh, p.material))
        scene.node(Node(f"{p.name} node", mesh=p.name), h.name)
    cyl = _cylinder(0.0019, 16)
    scene.mesh(Mesh("cable", *cyl, "rope"))
    scene.node(Node("cable", mesh="cable", translation=tuple(port_world)))

    if ex is None:
        bar = port_world + np.array([0.0, 0.0, 0.06])
        h.translation = tuple(bar)
        _point_cable(scene, port_world, bar[None, :], None)
        return scene, report

    # mannequin
    rig = mq.add_to_scene(scene, "human_")
    scene.nodes[rig.root].translation = tuple(human_pos)
    scene.nodes[rig.root].rotation = tuple(yaw)
    rel = mq.relative_rotations(poses)
    for seg, names in rig.joints.items():
        for name in names:
            scene.animate(ex.name, Channel(name, "rotation", t, rel[seg]))
    scene.animate(ex.name, Channel(rig.pelvis, "translation", t, ground))

    # bar follows the grip; the handle's eye points at the cable port
    bar = grip_world
    scene.animate(ex.name, Channel("handle", "translation", t, bar))
    to_port = port_world - bar
    ang = np.arctan2(-to_port[:, 1], to_port[:, 2])  # rotate about X so the eye (+Z local) faces the port
    scene.animate(ex.name, Channel("handle", "rotation", t, quat_axis_angle([1.0, 0, 0], ang)))
    start = port_world
    run = 0.0
    if ex.redirect:  # floor pulley under the bar's start position; the floor run is fixed
        pr = 0.035
        centre = np.array([0.0, port_world[1] + pr, bar[0, 2]])
        _pulley(scene, centre, pr)
        floor_end = centre + np.array([0.0, -pr, 0.0])
        _fixed_cable(scene, "cable floor run", port_world, floor_end)
        run = float(np.linalg.norm(floor_end - port_world)) + np.pi * pr / 2
        start = centre + np.array([0.0, pr, 0.0])
        scene.nodes["cable"].translation = tuple(start)
    payout = _point_cable(scene, start, bar, (ex.name, t)) + run
    r = info["drum_radius_mm"] / 1000.0
    drum_angle = -(payout - payout.min()) / r
    scene.animate(ex.name, Channel("drum", "rotation", t, quat_axis_angle([1.0, 0, 0], drum_angle)))
    for g in ("motor_left", "motor_right"):
        scene.animate(ex.name, Channel(g, "rotation", t, quat_axis_angle([1.0, 0, 0], info["ratio"] * drum_angle)))
    # Bake frame 0 into every animated node's static TRS so viewers without animation
    # playback (Golemics today) still show a coherent posed scene.
    for ch in scene.animations[ex.name]:
        attr = {"translation": "translation", "rotation": "rotation", "scale": "scale"}[ch.path]
        setattr(scene.nodes[ch.node], attr, tuple(float(v) for v in ch.values[0]))
    report.update({"duration_s": float(t[-1]), "frames": len(t), "stroke_m": float(payout.max() - payout.min()),
                   "peak_cable_speed_m_s": float(np.max(np.abs(np.gradient(payout, t)))),
                   "min_cable_length_m": float(payout.min()), "scenario": ex.scenario})
    return scene, report


def _point_cable(scene, port, bar, anim):
    d = bar - port
    length = np.linalg.norm(d, axis=1)
    q = quat_between([0, 1.0, 0], d)
    scales = np.stack([np.ones_like(length), length, np.ones_like(length)], axis=1)
    if anim is None:
        scene.nodes["cable"].rotation = tuple(q[0])
        scene.nodes["cable"].scale = tuple(scales[0])
    else:
        name, t = anim
        scene.animate(name, Channel("cable", "rotation", t, q))
        scene.animate(name, Channel("cable", "scale", t, scales))
    return length


def _cylinder(radius, sides):
    phi = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    ring = np.stack([np.cos(phi), np.zeros(sides), np.sin(phi)], axis=1)
    pos = np.concatenate([ring * radius, ring * radius + [0, 1.0, 0]])
    nrm = np.concatenate([ring, ring])
    j = np.arange(sides)
    k = (j + 1) % sides
    idx = np.stack([j, j + sides, k, k, j + sides, k + sides], axis=1).reshape(-1)
    return pos.astype(np.float32), nrm.astype(np.float32), idx.astype(np.uint32)


def _box(scene, name, size, centre, material):
    sx, sy, sz = (v / 2 for v in size)
    faces = [((1, 0, 0), sx), ((-1, 0, 0), sx), ((0, 1, 0), sy), ((0, -1, 0), sy), ((0, 0, 1), sz), ((0, 0, -1), sz)]
    pos, nrm, idx = [], [], []
    for n, _ in faces:
        n = np.array(n, float)
        a = np.array([n[1], n[2], n[0]])
        b = np.cross(n, a)
        half = np.array([sx, sy, sz])
        corners = [n * half + (sa * a + sb * b) * half for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        base = len(pos)
        pos += corners
        nrm += [n] * 4
        idx += [base, base + 1, base + 2, base, base + 2, base + 3]
    p = np.array(pos, np.float32)
    nr = np.array(nrm, np.float32)
    ix = np.array(idx, np.uint32)
    # make winding match the normal
    tri = p[ix.reshape(-1, 3)]
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    flip = np.sum(fn * nr[ix.reshape(-1, 3)[:, 0]], axis=1) < 0
    t3 = ix.reshape(-1, 3)
    t3[flip] = t3[flip][:, [0, 2, 1]]
    scene.mesh(Mesh(name, p, nr, t3.reshape(-1), material))
    scene.node(Node(name, mesh=name, translation=tuple(centre)))


def bottom_clearance(ex: Exercise) -> float:
    """Smallest forward gap (m) between the bar and the shin line during the motion (deadlift sanity)."""
    gaps = []
    for u in np.linspace(0, 1, 21):
        j = mq.fk(mq.interpolate(ex.start, ex.end, u))
        knee, ankle, grip = j["knee"], j["ankle"], j["grip"]
        if knee[1] > grip[1] > ankle[1]:
            f = (grip[1] - ankle[1]) / (knee[1] - ankle[1])
            shin_z = ankle[2] + f * (knee[2] - ankle[2])
            gaps.append(grip[2] - shin_z)
    return float(min(gaps)) if gaps else float("inf")


def _fixed_cable(scene, name, a, b):
    cyl = _cylinder(0.0019, 16)
    scene.mesh(Mesh(name, *cyl, "rope"))
    d = np.asarray(b) - np.asarray(a)
    scene.node(Node(name, mesh=name, translation=tuple(a), rotation=tuple(quat_between([0, 1.0, 0], d[None, :])[0]),
                    scale=(1.0, float(np.linalg.norm(d)), 1.0)))


def _pulley(scene, centre, r):
    """Floor redirect pulley: a sheave in a fork on a base plate (visual only)."""
    import cadquery as cq
    mm = r * 1000
    sheave = (cq.Workplane("YZ").circle(mm).circle(6).extrude(14).translate((-7, 0, 0))
              .cut(cq.Workplane("XY").box(2, 1, 1)))  # trivial cut keeps a solid
    groove = cq.Workplane("XZ").circle(mm + 1).extrude(1)  # noqa: F841 (visual simplicity)
    fork = (cq.Workplane("XY").box(30, 2 * mm + 20, mm + 12, centered=(True, True, False)).translate((0, 0, -mm - 12))
            .cut(cq.Workplane("XY").box(18, 2 * mm + 30, mm + 30, centered=(True, True, False)).translate((0, 0, -mm - 6))))
    base = cq.Workplane("XY").box(70, 90, 8, centered=(True, True, False)).translate((0, 0, -mm - 20)).edges("|Z").fillet(6)
    for name, shape, mat in (("pulley sheave", sheave, "alu"), ("pulley fork", fork, "graphite"),
                             ("pulley base", base, "dark_steel")):
        mesh = visual.tessellate(shape)
        scene.mesh(Mesh(name, *mesh, mat))
        scene.node(Node(name, mesh=name, translation=tuple(centre)))
