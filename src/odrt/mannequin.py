"""Mock human: rigid-segment mannequin with sagittal-plane forward kinematics.

Not a biomechanical model: segment lengths are rough adult proportions (1.75 m)
and poses are keyframes interpolated by the scenario's motion profile. Its only
job is to show plausible exercise motion and to place the handle (A-020).

Frame: glTF metres, Y up, the mannequin faces +Z in its own frame. Every joint
rotates about X only. Angles are world pitch angles in the mannequin frame:
"lean" tilts an upward segment forward, "fwd" swings a downward segment forward.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from odrt.gltf import Mesh, Node, quat_axis_angle

SEG = {"lumbar": 0.12, "thorax": 0.38, "neck": 0.09, "upper_arm": 0.29, "forearm": 0.26, "hand": 0.08,
       "thigh": 0.43, "shin": 0.43, "ankle_h": 0.08, "hip_half": 0.09, "shoulder_half": 0.18}
POSE_KEYS = ("pelvis_lean", "torso_lean", "thigh_fwd", "shin_fwd", "upper_arm_fwd", "forearm_fwd")


def _rot(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def world_angles(pose: dict) -> dict:
    """Rotation angles about X (radians) for each segment, from a pose in degrees."""
    d = {k: np.radians(pose[k]) for k in POSE_KEYS}
    return {"pelvis": d["pelvis_lean"], "torso": d["torso_lean"], "thigh": -d["thigh_fwd"], "shin": -d["shin_fwd"],
            "foot": 0.0, "upper_arm": -d["upper_arm_fwd"], "forearm": -d["forearm_fwd"],
            "hand": -d["forearm_fwd"], "head": d["torso_lean"]}


def fk(pose: dict) -> dict:
    """Joint positions in the mannequin frame with the pelvis at the origin (sagittal, x = 0)."""
    a = world_angles(pose)
    up, down = np.array([0, 1.0, 0]), np.array([0, -1.0, 0])
    p = {"pelvis": np.zeros(3)}
    p["chest"] = p["pelvis"] + _rot(a["pelvis"]) @ (SEG["lumbar"] * up)
    p["shoulder"] = p["chest"] + _rot(a["torso"]) @ (SEG["thorax"] * up)
    p["elbow"] = p["shoulder"] + _rot(a["upper_arm"]) @ (SEG["upper_arm"] * down)
    p["wrist"] = p["elbow"] + _rot(a["forearm"]) @ (SEG["forearm"] * down)
    p["grip"] = p["wrist"] + _rot(a["hand"]) @ (SEG["hand"] * down)
    p["knee"] = p["pelvis"] + _rot(a["thigh"]) @ (SEG["thigh"] * down)
    p["ankle"] = p["knee"] + _rot(a["shin"]) @ (SEG["shin"] * down)
    return p


def grounded_pelvis(pose: dict, ankle_z: float = 0.0) -> np.ndarray:
    """Pelvis position (mannequin frame) that puts the ankle at height ankle_h and depth ankle_z."""
    ankle = fk(pose)["ankle"]
    return np.array([0.0, SEG["ankle_h"] - ankle[1], ankle_z - ankle[2]])


def interpolate(a: dict, b: dict, u) -> dict:
    u = np.asarray(u, dtype=float)
    return {k: a[k] + (b[k] - a[k]) * u for k in POSE_KEYS}


# ---------------------------------------------------------------- meshes
def ellipsoid(rx, ry, rz, centre=(0, 0, 0), n_lat=14, n_lon=20):
    lat = np.linspace(-np.pi / 2, np.pi / 2, n_lat)
    lon = np.linspace(0, 2 * np.pi, n_lon, endpoint=False)
    la, lo = np.meshgrid(lat, lon, indexing="ij")
    unit = np.stack([np.cos(la) * np.cos(lo), np.sin(la), np.cos(la) * np.sin(lo)], axis=-1).reshape(-1, 3)
    pos = unit * np.array([rx, ry, rz]) + np.array(centre)
    nrm = unit / np.array([rx, ry, rz])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    i, j = np.meshgrid(np.arange(n_lat - 1), np.arange(n_lon), indexing="ij")
    a = i * n_lon + j
    b = i * n_lon + (j + 1) % n_lon
    c = (i + 1) * n_lon + j
    d = (i + 1) * n_lon + (j + 1) % n_lon
    idx = np.stack([a, b, c, b, d, c], axis=-1).reshape(-1)
    return pos.astype(np.float32), nrm.astype(np.float32), idx.astype(np.uint32)


def capsule(length, r_top, r_bottom, direction=-1, sx=1.0, sz=1.0, bulge=0.12, n_ring=24, n_len=36):
    """Smooth tapered capsule from the joint (origin) along direction*Y, with rounded ends.

    Cross-sections may be elliptical (sx, sz); `bulge` swells the middle like a muscle belly.
    Normals are averaged face normals, so the surface shades smoothly.
    """
    # arc-length style parameter: top cap, shaft, bottom cap
    s = np.linspace(0.0, 1.0, n_len)
    y_top, y_bot = r_top * 0.5, -(length + r_bottom * 0.5)
    y = y_top + (y_bot - y_top) * s
    lin = np.clip((-y) / length, 0.0, 1.0)
    rad = r_top + (r_bottom - r_top) * lin
    rad = rad * (1.0 + bulge * np.sin(np.pi * lin))
    # round the ends: shrink radius smoothly to 0 inside each cap
    top_cap = np.clip((y_top - y) / (r_top * 1.0), 0, 1)
    bot_cap = np.clip((y - y_bot) / (r_bottom * 1.0), 0, 1)
    rad = rad * np.sqrt(np.clip(1 - (1 - top_cap) ** 2, 0, 1)) * np.sqrt(np.clip(1 - (1 - bot_cap) ** 2, 0, 1))
    phi = np.linspace(0, 2 * np.pi, n_ring, endpoint=False)
    P = np.stack([sx * rad[:, None] * np.cos(phi)[None, :], np.repeat(y[:, None], n_ring, 1),
                  sz * rad[:, None] * np.sin(phi)[None, :]], axis=-1)
    if direction > 0:
        P[..., 1] *= -1
    pos = P.reshape(-1, 3)
    i, j = np.meshgrid(np.arange(n_len - 1), np.arange(n_ring), indexing="ij")
    a = i * n_ring + j
    b = i * n_ring + (j + 1) % n_ring
    c = (i + 1) * n_ring + j
    d = (i + 1) * n_ring + (j + 1) % n_ring
    tri = np.stack([a, b, c, b, d, c], axis=-1).reshape(-1, 3)
    if direction > 0:
        tri = tri[:, [0, 2, 1]]
    return pos.astype(np.float32), smooth_normals(pos, tri), tri.reshape(-1).astype(np.uint32)


def smooth_normals(pos, tri):
    fn = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    vn = np.zeros_like(pos)
    for k in range(3):
        np.add.at(vn, tri[:, k], fn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
    return vn.astype(np.float32)


def limb(length, r_top, r_bottom, direction=-1):
    return capsule(length, r_top, r_bottom, direction)


def merge(parts):
    pos, nrm, idx, base = [], [], [], 0
    for p, n, i in parts:
        pos.append(p)
        nrm.append(n)
        idx.append(i + base)
        base += len(p)
    return np.concatenate(pos), np.concatenate(nrm), np.concatenate(idx)


@dataclass
class Rig:
    root: str          # node carrying world placement (translation + yaw)
    pelvis: str
    joints: dict       # segment name -> node name(s)


def add_to_scene(scene, prefix: str, material: str = "skin") -> Rig:
    """Adds mannequin meshes and the node hierarchy; returns node names for animation."""
    meshes = {
        "pelvis": merge([ellipsoid(0.165, 0.1, 0.11, (0, 0.03, 0), 18, 26)]),
        "torso": capsule(SEG["thorax"] - 0.02, 0.105, 0.13, direction=+1, sx=1.45, sz=0.8, bulge=0.1),
        "head": merge([capsule(0.07, 0.045, 0.045, direction=+1, bulge=0.0),
                       ellipsoid(0.085, 0.11, 0.1, (0, 0.17, 0.012), 22, 28)]),
        "upper_arm": limb(SEG["upper_arm"], 0.05, 0.04),
        "forearm": limb(SEG["forearm"], 0.04, 0.03),
        "hand": merge([ellipsoid(0.025, 0.05, 0.042, (0, -0.045, 0), 14, 18)]),
        "thigh": limb(SEG["thigh"], 0.075, 0.055),
        "shin": limb(SEG["shin"], 0.05, 0.035),
        "foot": merge([ellipsoid(0.045, 0.035, 0.125, (0, -0.045, 0.05), 14, 22)]),
    }
    for name, (p, n, i) in meshes.items():
        scene.mesh(Mesh(f"{prefix}{name}", p, n, i, material))
    root = scene.node(Node(f"{prefix}root"))
    pelvis = scene.node(Node(f"{prefix}pelvis", mesh=f"{prefix}pelvis"), root.name)
    torso = scene.node(Node(f"{prefix}torso", mesh=f"{prefix}torso", translation=(0, SEG["lumbar"], 0)), pelvis.name)
    scene.node(Node(f"{prefix}head", mesh=f"{prefix}head", translation=(0, SEG["thorax"] + 0.02, 0)), torso.name)
    joints = {"pelvis": [pelvis.name], "torso": [torso.name], "upper_arm": [], "forearm": [], "hand": [],
              "thigh": [], "shin": [], "foot": []}
    for side, sx in (("l", 1), ("r", -1)):
        ua = scene.node(Node(f"{prefix}upper_arm_{side}", mesh=f"{prefix}upper_arm",
                             translation=(sx * SEG["shoulder_half"], SEG["thorax"], 0)), torso.name)
        fa = scene.node(Node(f"{prefix}forearm_{side}", mesh=f"{prefix}forearm",
                             translation=(0, -SEG["upper_arm"], 0)), ua.name)
        ha = scene.node(Node(f"{prefix}hand_{side}", mesh=f"{prefix}hand", translation=(0, -SEG["forearm"], 0)), fa.name)
        th = scene.node(Node(f"{prefix}thigh_{side}", mesh=f"{prefix}thigh",
                             translation=(sx * SEG["hip_half"], 0, 0)), pelvis.name)
        sh = scene.node(Node(f"{prefix}shin_{side}", mesh=f"{prefix}shin", translation=(0, -SEG["thigh"], 0)), th.name)
        ft = scene.node(Node(f"{prefix}foot_{side}", mesh=f"{prefix}foot", translation=(0, -SEG["shin"], 0)), sh.name)
        for seg, node in (("upper_arm", ua), ("forearm", fa), ("hand", ha), ("thigh", th), ("shin", sh), ("foot", ft)):
            joints[seg].append(node.name)
    return Rig(root=root.name, pelvis=pelvis.name, joints=joints)


PARENT = {"pelvis": None, "torso": "pelvis", "upper_arm": "torso", "forearm": "upper_arm", "hand": "forearm",
          "thigh": "pelvis", "shin": "thigh", "foot": "shin"}


def relative_rotations(poses: dict) -> dict:
    """Per-segment local quaternions (k, 4) from per-frame poses (arrays of degrees)."""
    a = world_angles(poses)
    out = {}
    for seg, parent in PARENT.items():
        rel = a[seg] - (a[parent] if parent else 0.0)
        out[seg] = quat_axis_angle([1.0, 0, 0], rel)
    return out
