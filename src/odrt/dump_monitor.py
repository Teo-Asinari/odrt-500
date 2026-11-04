"""Supervisor dump-path monitor, layered on a coupled model factory (R4).

The supervisor knows the chopper duty it commands from the bus voltage, so it
expects a dump current of duty x bus V / R. A shunt measures the actual
current; after a dump_failure fault the measurement is zero. A per-unit timer
state integrates while the fault condition holds and resets quickly when it
clears. When it reaches the detection time, a zero-crossing event latches a
'dump_fault' trip through the same transition as the voltage/thermal trips.

    condition = (expected > min_expected and measured < fraction x expected)
                or bus V > backup_bus_v

Parameters live in data/r4_power.yaml (functions.dump_monitor). Without a
`measurement` block the monitor is ideal apart from its timing. With one, the
supervisor works from its own measurements and assumptions:

    measured current = (1 + current_gain) x true + current_offset + noise, low-pass filtered
    measured bus V   = (1 + voltage_gain) x true + voltage_offset + noise, low-pass filtered
    expected current = duty(measured V; assumed thresholds) x measured V / assumed R

The plant's actual chopper thresholds and resistance (cfg['power']) may differ
from the supervisor's `assumed` values, which is how threshold and resistor
tolerances enter. Noise is a seeded, sampled Gaussian sequence, linearly
interpolated (deterministic and reproducible, not a stochastic integrator).
"""
from __future__ import annotations

import numpy as np

from odrt.coupled import GLOBAL_FIELDS, MARGIN_EVENTS, TRIP_REASONS, scenario_duration_s


def _noise(ca, name, sigma, sample_s, duration_s, seed):
    if sigma == 0:
        return lambda t: 0
    grid = np.arange(0, duration_s+2*sample_s, sample_s)
    values = sigma*np.random.default_rng(seed).standard_normal(grid.size)
    table = ca.interpolant(name, 'linear', [grid], values)
    return lambda t: table(t)


def dump_monitor_factory(base_factory):
    def build(cfg, parts, scenario, defaults, stroke_m, case, **perturbations):
        import casadi as ca
        original = base_factory(cfg, parts, scenario, defaults, stroke_m, case, **perturbations)
        mon = cfg['dump_monitor']; p = cfg['power']; n = case['units']
        old_fields = tuple(original['unit_fields']); old_size = len(old_fields)
        meas = mon.get('measurement'); assumed = mon.get('assumed', {'dump_start_v': p['dump_start_v'],
            'dump_full_v': p['dump_full_v'], 'dump_resistance_ohm': p['dump_resistance_ohm']})
        fields = old_fields+('dump_timer_s',)+(('dump_meas_a', 'bus_meas_v') if meas else ()); size = len(fields)
        duration = case.get('window_s', scenario_duration_s(scenario, defaults))
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
            true_i = observables[prefix+'dump_w']/ca.fmax(vb, 1e-9)
            if meas:
                seed = meas['noise']['seed']+101*i
                ni = _noise(ca, f'i_noise_{i}', meas['noise']['current_sigma_a'], meas['noise']['sample_s'], duration, seed)
                nv = _noise(ca, f'v_noise_{i}', meas['noise']['voltage_sigma_v'], meas['noise']['sample_s'], duration, seed+1)
                raw_i = (1+meas['current_gain'])*true_i+meas['current_offset_a']+ni(t)
                raw_v = (1+meas['voltage_gain'])*vb+meas['voltage_offset_v']+nv(t)
                measured, vm = x[base+old_size+1], x[base+old_size+2]
                filters = [(raw_i-measured)/meas['filter_s'], (raw_v-vm)/meas['filter_s']]
                filter0 = [meas['current_offset_a'], (1+meas['voltage_gain'])*p['nominal_v']+meas['voltage_offset_v']]
            else:
                measured, vm, filters, filter0 = true_i, vb, [], []
            source = mon.get('duty_source', 'estimated')
            if source == 'gate':
                # The supervisor reads the chopper's own gate command. A failed open resistor or switch keeps the
                # gate active with no current; a gate-driver failure removes it and is left to the backup threshold.
                duty = ca.fmin(ca.fmax((vb-p['dump_start_v'])/(p['dump_full_v']-p['dump_start_v']), 0), 1)
            elif source == 'estimated':
                margin = mon.get('estimate_margin_v', 0.)
                start, full = assumed['dump_start_v']+margin, assumed['dump_full_v']+margin
                duty = ca.fmin(ca.fmax((vm-start)/(full-start), 0), 1)
            else:
                raise ValueError(f'dump monitor: unknown duty source {source!r}')
            expected = duty*vm/assumed['dump_resistance_ohm']
            condition = ca.logic_or(ca.logic_and(expected > mon['min_expected_a'], measured < mon['measured_fraction']*expected),
                                    vm > mon['backup_bus_v'])
            rhs += list(ca.vertsplit(old_ode[old_base:old_base+old_size]))
            rhs.append(ca.if_else(condition, 1, -timer/mon['reset_s']))
            rhs += filters
            initial += list(original['state0'][old_base:old_base+old_size])+[0.]+filter0
            zeros.append(ca.if_else(latched, 1, mon['detection_s']-timer))
            timers.append(timer)
            observables[prefix+'dump_expected_a'] = expected
            observables[prefix+'dump_measured_a'] = measured
            observables[prefix+'dump_monitor_condition'] = condition
            observables[prefix+'dump_true_a'] = true_i
            observables[prefix+'bus_measured_v'] = vm
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
            extra = [x[4+i*size+old_size+1+j] for j in range(size-old_size-1)]
            units.append(ca.vertcat(*block, ca.if_else(own, 0, timers[i]), *extra))
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
