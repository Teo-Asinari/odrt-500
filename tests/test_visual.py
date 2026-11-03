"""glTF writer, mannequin kinematics and animation consistency."""
import json
import struct

import numpy as np
import pytest

from odrt import mannequin as mq
from odrt.gltf import Channel, Material, Mesh, Node, Scene, quat_axis_angle, quat_between, quat_rotate


def _tri():
    p = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], np.float32)
    return Mesh("t", p, np.tile([0, 0, 1.0], (3, 1)).astype(np.float32), np.array([0, 1, 2], np.uint32), "m")


def test_glb_structure_and_animation():
    s = Scene()
    s.material(Material("m", (1, 0, 0, 1)))
    s.mesh(_tri())
    s.node(Node("a", mesh="t"))
    s.node(Node("b", mesh="t", translation=(1, 0, 0)), "a")
    t = np.array([0.0, 1.0])
    s.animate("spin", Channel("b", "rotation", t, quat_axis_angle([0, 1, 0], [0.0, 1.0])))
    glb = s.to_glb()
    assert glb[:4] == b"glTF" and struct.unpack("<I", glb[8:12])[0] == len(glb)
    n = struct.unpack("<I", glb[12:16])[0]
    g = json.loads(glb[20:20 + n])
    assert g["nodes"][0]["children"] == [1]
    ch = g["animations"][0]["channels"][0]
    assert ch["target"] == {"node": 1, "path": "rotation"}
    assert g["accessors"][g["animations"][0]["samplers"][0]["input"]]["max"] == [1.0]


def test_unknown_material_or_node_rejected():
    s = Scene()
    with pytest.raises(KeyError):
        s.mesh(_tri())
    with pytest.raises(KeyError):
        s.animate("x", Channel("nope", "scale", np.zeros(1), np.ones((1, 3))))


def test_quaternion_helpers():
    q = quat_between([0, 1.0, 0], np.array([[1.0, 0, 0], [0, -1.0, 0]]))
    out = quat_rotate(q, np.array([[0, 1.0, 0], [0, 1.0, 0]]))
    np.testing.assert_allclose(out, [[1, 0, 0], [0, -1, 0]], atol=1e-12)


def test_limb_lengths_preserved_by_fk():
    pose = {"pelvis_lean": 40, "torso_lean": 45, "thigh_fwd": 60, "shin_fwd": -20, "upper_arm_fwd": 30, "forearm_fwd": 90}
    j = mq.fk(pose)
    for a, b, seg in (("shoulder", "elbow", "upper_arm"), ("elbow", "wrist", "forearm"), ("pelvis", "knee", "thigh"),
                      ("knee", "ankle", "shin")):
        assert np.linalg.norm(j[b] - j[a]) == pytest.approx(mq.SEG[seg])


def test_grounding_keeps_ankle_fixed():
    for pose in ({k: 0.0 for k in mq.POSE_KEYS},
                 {"pelvis_lean": 50, "torso_lean": 55, "thigh_fwd": 60, "shin_fwd": -20, "upper_arm_fwd": 0,
                  "forearm_fwd": 0}):
        g = mq.grounded_pelvis(pose)
        ankle = mq.fk(pose)["ankle"] + g
        np.testing.assert_allclose(ankle, [0, mq.SEG["ankle_h"], 0], atol=1e-12)


def test_relative_rotations_reproduce_world_angles():
    pose = {k: np.array([10.0 * (i + 1)]) for i, k in enumerate(mq.POSE_KEYS)}
    rel = mq.relative_rotations(pose)
    # composing pelvis -> thigh -> shin local rotations gives the shin's world angle
    from odrt.gltf import quat_mul
    q = quat_mul(quat_mul(rel["pelvis"], rel["thigh"]), rel["shin"])
    expected = quat_axis_angle([1.0, 0, 0], mq.world_angles(pose)["shin"])
    np.testing.assert_allclose(np.abs(np.sum(q * expected, axis=-1)), 1.0, atol=1e-12)


def test_deadlift_bar_clears_shins():
    from odrt.animate import EXERCISES, bottom_clearance
    dl = [e for e in EXERCISES if e.name == "deadlift"][0]
    assert bottom_clearance(dl) > 0.0


@pytest.mark.slow
def test_static_pose_matches_first_frame():
    pytest.importorskip("cadquery")
    from conftest import REPO
    from odrt import animate, visual
    from odrt.cli import structural_summary
    from odrt.project import load_inputs
    inputs = load_inputs(REPO)
    st = inputs.structure
    parts, pivots, info = visual.build(st, inputs.options[st.design], inputs.common, structural_summary(inputs, {}))
    ex = animate.EXERCISES[0]
    scene, _ = animate.build_scene(inputs, parts[:3], pivots, info, visual.handle()[:1], ex)
    for ch in scene.animations[ex.name]:
        static = np.array(getattr(scene.nodes[ch.node], ch.path))
        np.testing.assert_allclose(static, ch.values[0], atol=1e-6)
