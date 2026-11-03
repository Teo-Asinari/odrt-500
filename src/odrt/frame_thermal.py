"""Conducted motor-to-frame heat path, layered on any coupled model factory.

Adds one lumped 'frame' node per unit: the motor housing conducts into the
stator carrier/base/skin through R_hf; the frame loses heat to the room by
external natural convection + radiation (G_fr) and to the internal air by the
forced flow over its inner faces (G_fa). Energy storage and the ambient-heat
quadrature are extended consistently, so the energy residual still audits it.
Every parameter is an explicit proposal in data/r3_thermal.yaml.
"""
from __future__ import annotations

import numpy as np

from odrt.coupled import GLOBAL_FIELDS


def frame_factory(base_factory):
    def build(cfg, parts, scenario, defaults, stroke_m, case, **perturbations):
        import casadi as ca
        original = base_factory(cfg, parts, scenario, defaults, stroke_m, case, **perturbations)
        f = cfg['frame_thermal']; n = case['units']
        old_fields = tuple(original['unit_fields']); old_size = len(old_fields)
        fields = old_fields + ('frame_c',); size = len(fields)
        ambient = cfg['thermal']['ambient_c'] + perturbations.get('ambient_offset_c', 0.)
        x = ca.SX.sym('frame_state', 4+n*size); t = original['t']; parameter = original['p']
        projected = ca.vertcat(x[:4], *[x[4+i*size:4+i*size+old_size] for i in range(n)])
        sub = lambda expr: ca.substitute(expr, original['x'], projected)
        old_ode = sub(original['ode']); quad = sub(original['quad'])
        energy = original['energy'](projected)
        observables = dict(zip(original['observable_names'],
                               ca.vertsplit(original['observables'](t, projected, parameter))))
        rhs = list(ca.vertsplit(old_ode[:4])); initial = list(original['state0'][:4])
        th = cfg['thermal']
        for i in range(n):
            base = 4+i*size; old_base = 4+i*old_size
            get = lambda field: x[base+old_fields.index(field)]
            housing, air, frame = get('housing_c'), get('air_c'), x[base+old_size]
            q_hf = (housing-frame)/f['housing_to_frame_k_w']
            q_fr = f['frame_to_room_w_k']*(frame-ambient)
            q_fa = f['frame_to_air_w_k']*(frame-air)
            local = list(ca.vertsplit(old_ode[old_base:old_base+old_size]))
            local[old_fields.index('housing_c')] -= q_hf/th['housing_capacity_j_k']
            local[old_fields.index('air_c')] += q_fa/th['air_capacity_j_k']
            rhs += local + [(q_hf-q_fr-q_fa)/f['frame_capacity_j_k']]
            quad[2] += q_fr
            energy += f['frame_capacity_j_k']*(frame-ambient)
            initial += list(original['state0'][old_base:old_base+old_size]) + [ambient]
            prefix = f'unit_{i}.'
            observables[prefix+'frame_c'] = frame
            observables[prefix+'frame_heat_in_w'] = q_hf
            observables[prefix+'frame_to_room_w'] = q_fr
        event_index = ca.SX.sym('event_index')
        post_old = original['transition'](event_index, t, projected)
        post = ca.vertcat(post_old[:4], *[ca.vertcat(post_old[4+i*old_size:4+(i+1)*old_size], x[4+i*size+old_size])
                                          for i in range(n)])
        ode = ca.vertcat(*rhs)
        model = dict(original)
        model.update(x=x, ode=ode, quad=quad, energy=ca.Function('frame_energy', [x], [energy]),
                     observables=ca.Function('frame_observables', [t, x, parameter], [ca.vertcat(*observables.values())]),
                     observable_names=list(observables),
                     state_names=list(GLOBAL_FIELDS)+[f'unit_{i}.{k}' for i in range(n) for k in fields],
                     state0=np.array(initial), unit_fields=fields, zero=sub(original['zero']),
                     transition=ca.Function('frame_transition', [event_index, t, x], [post]),
                     normal_targets=ca.Function('frame_targets', [t, x], [original['normal_targets'](t, projected)]),
                     rhs=ca.Function('frame_rhs', [t, x, parameter], [ode, quad]))
        return model
    return build
