"""Supervisor dump-path monitor, layered on a coupled model factory (R4).

The supervisor knows the chopper duty it commands from the bus voltage, so it
expects a dump current of duty x bus V / R. A shunt measures the actual
current; after a dump_failure fault the measurement is zero. A per-unit timer
state integrates while the fault condition holds and resets quickly when it
clears. When it reaches the detection time, a zero-crossing event latches a
'dump_fault' trip through the same transition as the voltage/thermal trips.

    condition = (expected > min_expected and measured < fraction x expected)
                or bus V > backup_bus_v

Parameters live in data/r4_power.yaml (functions.dump_monitor). The monitor
is ideal apart from its timing: shunt noise, offset and ADC filtering are not
modelled, and the commanded duty is assumed known exactly.
"""
from __future__ import annotations

import numpy as np

from odrt.coupled import GLOBAL_FIELDS, MARGIN_EVENTS, TRIP_REASONS


def dump_monitor_factory(base_factory):
    def build(cfg, parts, scenario, defaults, stroke_m, case, **perturbations):
        import casadi as ca
        original = base_factory(cfg, parts, scenario, defaults, stroke_m, case, **perturbations)
        mon = cfg['dump_monitor']; p = cfg['power']; n = case['units']
        old_fields = tuple(original['unit_fields']); old_size = len(old_fields)
        fields = old_fields+('dump_timer_s',); size = len(fields)
        x = ca.SX.sym('monitor_state', 4+n*size); t = original['t']; parameter = original['p']
        projected = ca.vertcat(x[:4], *[x[4+i*size:4+i*size+old_size] for i in range(n)])
        sub = lambda expr: ca.substitute(expr, original['x'], projected)
        old_ode = sub(original['ode'])
        observables = dict(zip(original['observable_names'],
                               ca.vertsplit(original['observables'](t, projected, parameter))))
        rhs = list(ca.vertsplit(old_ode[:4])); initial = list(original['state0'][:4])
        base_zero = sub(original['zero'])
        if base_zero.numel() != n*MARGIN_EVENTS:
            raise ValueError('dump monitor expects the base voltage/thermal events only')
        zeros, timers = [], []
        for i in range(n):
            base = 4+i*size; old_base = 4+i*old_size; prefix = f'unit_{i}.'
            get = lambda field: x[base+old_fields.index(field)]
            vb, timer, latched = get('bus_v'), x[base+old_size], get('trip_latched') > .5
            duty = ca.fmin(ca.fmax((vb-p['dump_start_v'])/(p['dump_full_v']-p['dump_start_v']), 0), 1)
            expected = duty*vb/p['dump_resistance_ohm']
            measured = observables[prefix+'dump_w']/ca.fmax(vb, 1e-9)
            condition = ca.logic_or(ca.logic_and(expected > mon['min_expected_a'], measured < mon['measured_fraction']*expected),
                                    vb > mon['backup_bus_v'])
            rhs += list(ca.vertsplit(old_ode[old_base:old_base+old_size]))
            rhs.append(ca.if_else(condition, 1, -timer/mon['reset_s']))
            initial += list(original['state0'][old_base:old_base+old_size])+[0.]
            zeros.append(ca.if_else(latched, 1, mon['detection_s']-timer))
            timers.append(timer)
            observables[prefix+'dump_expected_a'] = expected
            observables[prefix+'dump_measured_a'] = measured
            observables[prefix+'dump_monitor_condition'] = condition
        event_index = ca.SX.sym('event_index')
        post_old = original['transition'](event_index, t, projected)
        reason = TRIP_REASONS.index('dump_fault')+1
        units = []
        for i in range(n):
            block = list(ca.vertsplit(post_old[4+i*old_size:4+(i+1)*old_size]))
            own = event_index == n*MARGIN_EVENTS+i
            fresh = ca.logic_and(own, block[old_fields.index('trip_latched')] < .5)
            for field, value in (('trip_latched', 1), ('trip_time_s', t), ('trip_reason', reason),
                                 ('integral_n', 0), ('torque_nm', 0)):
                k = old_fields.index(field); block[k] = ca.if_else(fresh, value, block[k])
            units.append(ca.vertcat(*block, ca.if_else(own, 0, timers[i])))
        post = ca.vertcat(post_old[:4], *units)
        ode = ca.vertcat(*rhs); quad = sub(original['quad'])
        model = dict(original)
        model.update(x=x, ode=ode, quad=quad, energy=ca.Function('monitor_energy', [x], [original['energy'](projected)]),
                     observables=ca.Function('monitor_observables', [t, x, parameter], [ca.vertcat(*observables.values())]),
                     observable_names=list(observables),
                     state_names=list(GLOBAL_FIELDS)+[f'unit_{i}.{k}' for i in range(n) for k in fields],
                     state0=np.array(initial), unit_fields=fields, zero=ca.vertcat(base_zero, *zeros),
                     transition=ca.Function('monitor_transition', [event_index, t, x], [post]),
                     normal_targets=ca.Function('monitor_targets', [t, x], [original['normal_targets'](t, projected)]),
                     rhs=ca.Function('monitor_rhs', [t, x, parameter], [ode, quad]))
        return model
    return build
