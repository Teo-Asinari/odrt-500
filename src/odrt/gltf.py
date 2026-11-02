"""Minimal glTF 2.0 binary (GLB) writer: meshes, PBR materials, node hierarchy, animations.

Written here instead of relying on an exporter so that every rotating part can be
its own node with a pivot, materials carry metallic/roughness (and optional
KHR_materials_transmission), and rigid-node TRS animation is possible.
Units: metres, Y up (glTF convention).
"""
from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class Material:
    name: str
    base_color: tuple            # RGBA, linear
    metallic: float = 0.0
    roughness: float = 0.5
    transmission: float = 0.0    # KHR_materials_transmission
    emissive: tuple = (0.0, 0.0, 0.0)


@dataclass
class Mesh:
    name: str
    positions: np.ndarray        # (n, 3) float32
    normals: np.ndarray          # (n, 3) float32
    indices: np.ndarray          # (m,) uint32
    material: str


@dataclass
class Node:
    name: str
    mesh: Optional[str] = None
    translation: tuple = (0.0, 0.0, 0.0)
    rotation: tuple = (0.0, 0.0, 0.0, 1.0)   # quaternion x, y, z, w
    scale: tuple = (1.0, 1.0, 1.0)
    children: list = field(default_factory=list)  # child node names


@dataclass
class Channel:
    node: str
    path: str                    # "translation", "rotation" or "scale"
    times: np.ndarray            # (k,) seconds
    values: np.ndarray           # (k, 3) or (k, 4)


class Scene:
    def __init__(self):
        self.materials: dict = {}
        self.meshes: dict = {}
        self.nodes: dict = {}     # insertion-ordered
        self.roots: list = []
        self.animations: dict = {}  # name -> [Channel]

    def material(self, m: Material):
        self.materials[m.name] = m

    def mesh(self, m: Mesh):
        if m.material not in self.materials:
            raise KeyError(f"mesh {m.name}: unknown material {m.material}")
        self.meshes[m.name] = m

    def node(self, n: Node, parent: Optional[str] = None):
        if n.name in self.nodes:
            raise KeyError(f"duplicate node {n.name}")
        self.nodes[n.name] = n
        if parent is None:
            self.roots.append(n.name)
        else:
            self.nodes[parent].children.append(n.name)
        return n

    def animate(self, name: str, channel: Channel):
        if channel.node not in self.nodes:
            raise KeyError(f"animation {name}: unknown node {channel.node}")
        self.animations.setdefault(name, []).append(channel)

    def to_glb(self) -> bytes:
        buf = bytearray()
        views, accessors = [], []

        def add(array, target=None, kind="VEC3", minmax=False):
            data = np.ascontiguousarray(array)
            while len(buf) % 4:
                buf.append(0)
            offset = len(buf)
            buf.extend(data.tobytes())
            view = {"buffer": 0, "byteOffset": offset, "byteLength": data.nbytes}
            if target:
                view["target"] = target
            views.append(view)
            comp = 5125 if data.dtype == np.uint32 else 5126
            acc = {"bufferView": len(views) - 1, "componentType": comp, "count": int(data.shape[0]), "type": kind}
            if minmax:
                acc["min"] = [float(v) for v in np.atleast_1d(data.min(axis=0))]
                acc["max"] = [float(v) for v in np.atleast_1d(data.max(axis=0))]
            accessors.append(acc)
            return len(accessors) - 1

        mat_index = {name: i for i, name in enumerate(self.materials)}
        materials, uses_transmission = [], False
        for m in self.materials.values():
            entry = {"name": m.name, "pbrMetallicRoughness": {
                "baseColorFactor": [float(c) for c in m.base_color], "metallicFactor": float(m.metallic),
                "roughnessFactor": float(m.roughness)}}
            if any(m.emissive):
                entry["emissiveFactor"] = [float(c) for c in m.emissive]
            if m.base_color[3] < 1.0:
                entry["alphaMode"] = "BLEND"
            if m.transmission > 0:
                entry["extensions"] = {"KHR_materials_transmission": {"transmissionFactor": float(m.transmission)}}
                uses_transmission = True
            materials.append(entry)

        mesh_index, meshes = {}, []
        for name, m in self.meshes.items():
            pos = add(m.positions.astype(np.float32), 34962, "VEC3", minmax=True)
            nrm = add(m.normals.astype(np.float32), 34962, "VEC3")
            idx = add(m.indices.astype(np.uint32), 34963, "SCALAR")
            mesh_index[name] = len(meshes)
            meshes.append({"name": name, "primitives": [{"attributes": {"POSITION": pos, "NORMAL": nrm},
                                                         "indices": idx, "material": mat_index[m.material]}]})

        node_index = {name: i for i, name in enumerate(self.nodes)}
        nodes = []
        for n in self.nodes.values():
            entry = {"name": n.name}
            if n.mesh is not None:
                entry["mesh"] = mesh_index[n.mesh]
            if any(abs(v) > 0 for v in n.translation):
                entry["translation"] = [float(v) for v in n.translation]
            if tuple(n.rotation) != (0.0, 0.0, 0.0, 1.0):
                entry["rotation"] = [float(v) for v in n.rotation]
            if tuple(n.scale) != (1.0, 1.0, 1.0):
                entry["scale"] = [float(v) for v in n.scale]
            if n.children:
                entry["children"] = [node_index[c] for c in n.children]
            nodes.append(entry)

        animations = []
        for name, channels in self.animations.items():
            samplers, chans = [], []
            for ch in channels:
                t = add(ch.times.astype(np.float32), None, "SCALAR", minmax=True)
                kind = "VEC4" if ch.values.shape[1] == 4 else "VEC3"
                v = add(ch.values.astype(np.float32), None, kind)
                samplers.append({"input": t, "output": v, "interpolation": "LINEAR"})
                chans.append({"sampler": len(samplers) - 1,
                              "target": {"node": node_index[ch.node], "path": ch.path}})
            animations.append({"name": name, "samplers": samplers, "channels": chans})

        gltf = {"asset": {"version": "2.0", "generator": "odrt gltf writer"},
                "scene": 0, "scenes": [{"nodes": [node_index[r] for r in self.roots]}],
                "nodes": nodes, "meshes": meshes, "materials": materials,
                "accessors": accessors, "bufferViews": views, "buffers": [{"byteLength": 0}]}
        if animations:
            gltf["animations"] = animations
        if uses_transmission:
            gltf["extensionsUsed"] = ["KHR_materials_transmission"]
        while len(buf) % 4:
            buf.append(0)
        gltf["buffers"][0]["byteLength"] = len(buf)
        js = json.dumps(gltf, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        total = 12 + 8 + len(js) + 8 + len(buf)
        return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<II", len(js), 0x4E4F534A) + js
                + struct.pack("<II", len(buf), 0x004E4942) + bytes(buf))


def quat_axis_angle(axis, angle) -> np.ndarray:
    """Quaternion(s) (x, y, z, w) for rotation by angle (rad, scalar or array) about a unit axis."""
    axis = np.asarray(axis, dtype=float)
    axis = axis / np.linalg.norm(axis)
    a = np.asarray(angle, dtype=float)[..., None]
    return np.concatenate([axis * np.sin(a / 2), np.cos(a / 2)], axis=-1)


def quat_between(u, v) -> np.ndarray:
    """Shortest-arc quaternion(s) rotating unit vector u onto v (v may be (k, 3))."""
    u = np.asarray(u, dtype=float) / np.linalg.norm(u)
    v = np.asarray(v, dtype=float)
    v = v / np.linalg.norm(v, axis=-1, keepdims=True)
    w = 1.0 + np.sum(u * v, axis=-1, keepdims=True)
    xyz = np.cross(u, v)
    q = np.concatenate([xyz, w], axis=-1)
    flip = w[..., 0] < 1e-9  # opposite vectors: rotate 180 deg about any axis perpendicular to u
    if np.any(flip):
        perp = np.cross(u, [1.0, 0, 0]) if abs(u[0]) < 0.9 else np.cross(u, [0, 1.0, 0])
        q[flip] = np.append(perp / np.linalg.norm(perp), 0.0)
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


def quat_mul(a, b) -> np.ndarray:
    ax, ay, az, aw = np.moveaxis(np.asarray(a, float), -1, 0)
    bx, by, bz, bw = np.moveaxis(np.asarray(b, float), -1, 0)
    return np.stack([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz], axis=-1)


def quat_rotate(q, v) -> np.ndarray:
    q = np.asarray(q, float)
    v = np.asarray(v, float)
    qv = np.concatenate([v, np.zeros(v.shape[:-1] + (1,))], axis=-1)
    conj = q * np.array([-1, -1, -1, 1])
    return quat_mul(quat_mul(q, qv), conj)[..., :3]
