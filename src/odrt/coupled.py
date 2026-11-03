"""Energy-accounted electromechanical reference plant for open resistance control.

Payout is positive. Motor torque is positive when resisting payout. A paired bar
has translation and rotation; its two cable endpoints can move independently.
Cables are unilateral and store elastic energy. Drum angle maps continuously to
payout through occupied winding layers. Electrical storage includes the real
series/parallel bank and a separate bus capacitor, joined by ESR. Every loss is
routed into a thermal state or explicitly recorded as heat leaving the system.

A virtual DC motor port uses tau=Kt*I, E=Kt*omega, R=(Kt/Km)^2. This is power
consistent, but mapping that equivalent current/voltage to the vendor's phase
conventions remains uncertain. Voltage saturation is a model screen, not a FOC
implementation. Protective delays are ideal proposals, not validated detection.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from odrt.config import ConfigError, check_keys, integer, load_yaml, number
from odrt.drivetrain import Architecture, Common, Drum
from odrt.engineering import load_engineering
from odrt.scenarios import _segments, scenario_duration_s
from odrt.units import lbf_to_n

UNIT_FIELDS = ('theta_rad', 'omega_rad_s', 'torque_nm', 'integral_n', 'force_sensor_n', 'speed_sensor_m_s',
               'capacitor_v', 'bus_v', 'winding_c', 'housing_c', 'drive_c', 'supply_c', 'capacitor_c', 'dump_c', 'air_c',
               'trip_latched', 'trip_time_s', 'trip_reason')
TRIP_REASONS = ('undervoltage', 'overvoltage', 'winding_temperature', 'drive_temperature', 'capacitor_temperature')
GLOBAL_FIELDS = ('bar_position_m', 'bar_speed_m_s', 'bar_angle_rad', 'bar_angular_speed_rad_s')
QUADRATURES = ('user_work_j', 'wall_input_j', 'ambient_heat_j')
FAULTS = ('none', 'mains_loss_braked', 'mains_loss_buffered', 'load_cell_zero', 'encoder_loss',
          'torque_inverted', 'torque_frozen', 'communication_loss', 'handle_release', 'emergency_stop', 'dump_failure')
GROUP_KEYS = {
    'reference': ('motor','drive','supply','rope','capacitor','ratio','efficiency','core_radius_mm','turns_per_layer',
                  'layers','dead_turns','drum_inertia_kg_m2','gear_transition_w'),
    'mechanics': ('routing_length_m','cable_ea_n','cable_damping_ratio','friction_n','friction_speed_m_s',
                  'single_handle_mass_kg','paired_bar_mass_kg','bar_half_span_m','bar_inertia_kg_m2',
                  'user_stiffness_n_m','user_damping_n_s_m','user_rot_stiffness_nm_rad','user_rot_damping_nm_s_rad',
                  'stop_stiffness_n_m','stop_damping_n_s_m'),
    'control': ('kp','ki_s','integral_limit_n','current_loop_s','force_filter_s','encoder_filter_s',
                'inertia_feedforward','current_limit_a','retract_speed_limit_m_s','retract_gain_n_s_m',
                'local_detection_s','peer_stop_delay_s','watchdog_s','rest_tension_n','winding_derate_c',
                'winding_stop_c','drive_derate_c','drive_stop_c'),
    'power': ('nominal_v','undervoltage_v','trip_v','dump_start_v','dump_full_v','dump_resistance_ohm',
              'bus_capacitance_f','cell_series','cell_parallel','supply_droop_ohm','drive_loss_fraction',
              'drive_idle_w','bleed_resistance_ohm','phase_brake_resistance_ohm'),
    'thermal': ('ambient_c','winding_to_housing_k_w','housing_to_air_k_w','winding_capacity_j_k',
                'housing_capacity_j_k','drive_to_air_k_w','drive_capacity_j_k','supply_to_air_k_w',
                'supply_capacity_j_k','dump_to_air_k_w','dump_capacity_j_k','air_capacity_j_k',
                'air_to_room_w_k','supply_derate_start_c','supply_stop_c'),
    'solver': ('relative_tolerance','absolute_tolerance','maximum_step_s','output_step_s','max_steps'),
}


# Optional controller features; defaults reproduce the reference controller exactly.
#   acceleration_blend: 0 = inertia feedforward on the scenario's planned acceleration,
#     1 = on the measured payout acceleration (derivative of the filtered encoder speed).
#   end_zone_m / end_zone_gain_n_s_m: within end_zone_m of either travel limit, the command
#     gains a velocity-proportional braking term toward that limit (0 disables).
OPTIONAL_KEYS = {'control': ('acceleration_blend', 'end_zone_m', 'end_zone_gain_n_s_m')}
CONTROL_DEFAULTS = {'acceleration_blend': 0., 'end_zone_m': 0., 'end_zone_gain_n_s_m': 0.}


def load_coupled(root, scenarios=None):
    root = Path(root)
    _, parts, _, _ = load_engineering(root)
    d = load_yaml(root/'configs/coupled.yaml')
    check_keys(d, 'coupled', list(GROUP_KEYS)+['cases'])
    names = ('motor','drive','supply','rope','capacitor')
    for group, fields in GROUP_KEYS.items():
        check_keys(d[group], 'coupled.'+group, fields, OPTIONAL_KEYS.get(group, ()))
        for field,value in d[group].items():
            if group == 'reference' and field in names:
                if value not in parts:
                    raise ConfigError(f'coupled.reference.{field}: unknown component {value}')
                expected = {'capacitor':'capacitor_cell'}.get(field,field)
                if parts[value]['role'] != expected:
                    raise ConfigError(f'coupled.reference.{field}: incorrect component role')
            else:
                number(value, f'coupled.{group}.{field}', minimum=0)
    for group, fields in {
        'mechanics': ('routing_length_m','cable_ea_n','friction_speed_m_s','single_handle_mass_kg',
                      'paired_bar_mass_kg','bar_half_span_m','bar_inertia_kg_m2','stop_stiffness_n_m'),
        'control': ('current_loop_s','force_filter_s','encoder_filter_s','current_limit_a'),
        'power': ('bus_capacitance_f','supply_droop_ohm','dump_resistance_ohm','bleed_resistance_ohm','phase_brake_resistance_ohm'),
        'thermal': tuple(k for k in d['thermal'] if k.endswith(('_k_w','_j_k','_w_k'))),
        'solver': tuple(d['solver']),
        'reference': ('ratio','efficiency','core_radius_mm','gear_transition_w'),
    }.items():
        for field in fields:
            number(d[group][field], f'{group}.{field}', minimum=0, exclusive_minimum=True)
    for group, fields in {'power':('cell_series','cell_parallel'),
                          'reference':('turns_per_layer','layers'), 'solver':('max_steps',)}.items():
        for field in fields:
            integer(d[group][field], f'{group}.{field}', minimum=1)
    integer(d['reference']['dead_turns'],'reference.dead_turns',minimum=0)
    if d['reference']['efficiency'] > 1:
        raise ConfigError('coupled efficiency must be <= 1')
    p = d['power']
    vmax = parts[d['reference']['drive']]['values']['voltage_absolute_max_v']
    if not 0 < p['undervoltage_v'] < p['nominal_v'] < p['dump_start_v'] < p['dump_full_v'] < p['trip_v'] < vmax:
        raise ConfigError('coupled voltage thresholds must be ordered and below drive absolute maximum')
    selected_fields = {
        'motor': ('inertia_kg_m2','kt_nm_per_a','km_nm_per_sqrt_w','torque_peak_nm','pole_pairs'),
        'drive': ('voltage_absolute_max_v','modulation_utilization','recommended_electrical_frequency_hz','ambient_max_c_for_ratings'),
        'supply': ('power_forced_air_w','efficiency_nominal'),
        'rope': ('diameter_mm','spliced_breaking_n'),
        'capacitor': ('capacitance_f','esr_initial_max_ohm','thermal_capacity_j_per_k',
                      'thermal_resistance_k_per_w','case_max_c','voltage_rated_v'),
    }
    for role,fields in selected_fields.items():
        missing = set(fields)-set(parts[d['reference'][role]]['values'])
        if missing:
            raise ConfigError(f'coupled {role}: required model data missing {sorted(missing)}')
    cell_max = parts[d['reference']['capacitor']]['values']['voltage_rated_v'] * p['cell_series']
    if p['trip_v'] >= cell_max:
        raise ConfigError('coupled bank voltage rating insufficient')
    for group,a,b in (('control','winding_derate_c','winding_stop_c'),('control','drive_derate_c','drive_stop_c'),
                      ('thermal','supply_derate_start_c','supply_stop_c')):
        if d[group][a] >= d[group][b]:
            raise ConfigError('coupled derating start must be below stop temperature')
    if not isinstance(d['cases'],list) or not d['cases']:
        raise ConfigError('coupled.cases: expected nonempty list')
    seen = set()
    for case in d['cases']:
        check_keys(case, 'coupled.case', ['name','scenario','units','fault'],
                   ['fault_time_s','window_s','peer_stop','command_scales'])
        if not isinstance(case['name'], str) or not case['name'] or case['name'] in seen:
            raise ConfigError('coupled case name missing or duplicate')
        seen.add(case['name'])
        if scenarios is not None and case['scenario'] not in scenarios:
            raise ConfigError('coupled case references unknown scenario')
        integer(case['units'],'case.units',minimum=1)
        if case['units'] not in (1,2) or case['fault'] not in FAULTS:
            raise ConfigError('coupled unit count or fault invalid')
        if case['fault'] != 'none' and 'fault_time_s' not in case:
            raise ConfigError('coupled fault_time_s required')
        for field in ('fault_time_s','window_s'):
            if field in case:
                number(case[field],field,minimum=0,exclusive_minimum=field=='window_s')
        if 'fault_time_s' in case and 'window_s' in case and case['fault_time_s'] >= case['window_s']:
            raise ConfigError('coupled fault must occur before window ends')
        if not isinstance(case.get('peer_stop',False),bool):
            raise ConfigError('coupled peer_stop must be boolean')
        scales = case.get('command_scales',[1]*case['units'])
        if not isinstance(scales,list) or len(scales)!=case['units']:
            raise ConfigError('coupled command_scales must match units')
        for value in scales:
            number(value,'command_scale',minimum=0,maximum=1)
    return d,parts


def winding_map(reference, rope_diameter_m, stroke_m):
    """Piecewise-linear payout(angle), plus its consistent derivative radius.

    Physical layer crossovers are idealized as radius steps, not smooth guides.
    Rotor angle and cable payout remain continuous and stored energy is retained.
    """
    arch = Architecture('coupled','coupled',reference['ratio'],reference['efficiency'],
                        reference['core_radius_mm']/1000,reference['turns_per_layer'],reference['layers'],
                        reference['drum_inertia_kg_m2'],0,1)
    drum = Drum(arch,Common(rope_diameter_m,reference['dead_turns'],25,60))
    drum.check_capacity(stroke_m,'coupled winding')
    breaks = sorted([0.,stroke_m]+[float(stroke_m+drum.dead_length_m-c) for c in drum.capacity
                                   if 0 < stroke_m+drum.dead_length_m-c < stroke_m])
    radii = [float(drum.radius((a+b)/2,stroke_m)) for a,b in zip(breaks[:-1],breaks[1:])]
    angles = [0.]
    for a,b,r in zip(breaks[:-1],breaks[1:],radii):
        angles.append(angles[-1]+(b-a)/r)
    return np.array(breaks),np.array(angles),np.array(radii)


def _reference(ca,t,scenario,defaults):
    result = ca.vertcat(scenario.start_offset_m,0,0,lbf_to_n(defaults.rest_tension_lbf))
    start = 0.
    previous = lbf_to_n(defaults.rest_tension_lbf)
    for _,duration,x0,x1,target_lbf in _segments(scenario,defaults):
        elapsed = ca.fmin(ca.fmax(t-start,0),duration)
        u = elapsed/duration
        span = x1-x0
        value = ca.vertcat(x0+span*u**3*(10-15*u+6*u**2),
                          span/duration*30*u**2*(1-u)**2,
                          span/duration**2*60*u*(1-u)*(1-2*u),
                          previous+(lbf_to_n(target_lbf)-previous)*ca.fmin(elapsed/defaults.tension_ramp_s,1))
        result = ca.if_else(t>=start,value,result)
        previous = lbf_to_n(target_lbf)
        start += duration
    return result


def build_model(cfg,parts,scenario,defaults,stroke_m,case,*,km_scale=1.,esr_scale=1.,capacitance_scale=1.,
                cable_ea_scale=1.,inertia_scale=1.,friction_scale=1.,ambient_offset_c=0.,user_stiffness_scale=1.,user_damping_scale=1.):
    """Return named symbolic state/observable/energy functions and initial state."""
    try:
        import casadi as ca
    except ImportError as exc:
        raise ConfigError('coupled simulation requires CasADi: install the [engineering] extra') from exc
    for scale in (km_scale,esr_scale,capacitance_scale,cable_ea_scale,inertia_scale,friction_scale,
                  user_stiffness_scale,user_damping_scale):
        number(scale,'coupled sensitivity scale',minimum=0,exclusive_minimum=True)
    n = case['units']
    ref,m,p,th = (cfg[k] for k in ('reference','mechanics','power','thermal'))
    c = {**CONTROL_DEFAULTS, **cfg['control']}
    motor,drive,supply,rope,cell = (parts[ref[k]]['values'] for k in ('motor','drive','supply','rope','capacitor'))
    xb,qb,radii = winding_map(ref,rope['diameter_mm']/1000,stroke_m)
    g,eta = ref['ratio'],ref['efficiency']
    rotor_j = (ref['drum_inertia_kg_m2']+g*g*motor['inertia_kg_m2'])*inertia_scale
    mass = m['single_handle_mass_kg'] if n==1 else m['paired_bar_mass_kg']
    bar_i = m['bar_inertia_kg_m2']
    half = 0 if n==1 else m['bar_half_span_m']
    cap_c = cell['capacitance_f']/p['cell_series']*p['cell_parallel']*capacitance_scale
    cap_r = cell['esr_initial_max_ohm']*p['cell_series']/p['cell_parallel']*esr_scale
    cap_heat_c = cell['thermal_capacity_j_per_k']*p['cell_series']*p['cell_parallel']
    cap_heat_r = cell['thermal_resistance_k_per_w']/(p['cell_series']*p['cell_parallel'])
    ambient = th['ambient_c']+ambient_offset_c
    t = ca.SX.sym('t')
    state_names = list(GLOBAL_FIELDS)+[f'unit_{i}.{field}' for i in range(n) for field in UNIT_FIELDS]
    x = ca.SX.sym('x',len(state_names))
    frozen_parameter = ca.SX.sym('frozen_command_nm',n)
    normal_targets, event_margins = [], []
    z,v,phi,w = ca.vertsplit(x[:4])
    reference = _reference(ca,t,scenario,defaults)
    xr,vr,ar,fr = ca.vertsplit(reference)
    scales = case.get('command_scales',[1]*n)
    fault = case['fault']
    tf = case.get('fault_time_s',1e20)
    live = t>tf if fault!='none' else ca.SX(0)
    released = live if fault=='handle_release' else ca.SX(0)
    user_force = (sum(scales)*fr + m['user_stiffness_n_m']*user_stiffness_scale*(xr-z)+m['user_damping_n_s_m']*user_damping_scale*(vr-v)+mass*ar)*(1-released)
    bias_moment = sum(((-1 if i==0 else 1) if n==2 else 0)*half*scales[i]*fr for i in range(n))
    user_moment = (bias_moment-m['user_rot_stiffness_nm_rad']*user_stiffness_scale*phi-m['user_rot_damping_nm_s_rad']*user_damping_scale*w)*(1-released)
    dz = [v,None,w if n==2 else 0,None]
    total_force,total_moment,ambient_power,contact_heat = 0,0,0,0
    storage = .5*mass*v*v + (.5*bar_i*w*w if n==2 else 0)
    wall_input = 0
    observables = {'reference_position_m':xr,'reference_speed_m_s':vr,'reference_force_n':fr,
                   'user_force_n':user_force,'user_moment_nm':user_moment}
    state0 = [scenario.start_offset_m,0.,0.,0.]

    def clamp(a,lo,hi):
        return ca.fmin(ca.fmax(a,lo),hi)

    def derate(temp,start,stop):
        return clamp((stop-temp)/(stop-start),0,1)

    def payout(theta):
        s = xb[0]+radii[0]*(theta-qb[0])
        r = ca.SX(radii[0])
        for j in range(1,len(radii)):
            s = ca.if_else(theta>=qb[j],xb[j]+radii[j]*(theta-qb[j]),s)
            r = ca.if_else(theta>=qb[j],radii[j],r)
        return s,r

    for i in range(n):
        u = dict(zip(UNIT_FIELDS,ca.vertsplit(x[4+i*len(UNIT_FIELDS):4+(i+1)*len(UNIT_FIELDS)])))
        theta,omega,tau = (u[k] for k in ('theta_rad','omega_rad_s','torque_nm'))
        vc,vb = u['capacitor_v'],u['bus_v']
        tw,hh,td,tp,tc,tr,ta = (u[k] for k in ('winding_c','housing_c','drive_c','supply_c','capacitor_c','dump_c','air_c'))
        s,r = payout(theta)
        vel = r*omega
        sign = (-1 if i==0 else 1) if n==2 else 0
        endpoint = z+sign*half*ca.sin(phi)
        endpoint_v = v+sign*half*ca.cos(phi)*w
        strain = ca.fmax(endpoint-s,0)
        length = m['routing_length_m']+ca.fmax(s,0)
        ea = m['cable_ea_n']*cable_ea_scale
        k = ea/length
        spring = k*strain
        mend = 1/(1/mass+(half*ca.cos(phi))**2/bar_i) if n==2 else mass
        meq = rotor_j/(r*r)
        damping = 2*m['cable_damping_ratio']*ca.sqrt(k/(1/meq+1/mend))
        tension = ca.if_else(strain>0,ca.fmax(0,spring+damping*(endpoint_v-vel)),0)
        # This length-dependent spring gradient is needed for power conservation.
        geometry_force = ca.if_else(s>0,.5*ea*strain*strain/(length*length),0)
        cable_heat = (tension-spring)*(endpoint_v-vel)
        storage += .5*ea*strain*strain/length + .5*rotor_j*omega*omega
        total_force += tension
        total_moment += sign*half*ca.cos(phi)*tension
        # Virtual compliant travel limits; actual arrestor and stops are not designed.
        penetration = ca.fmax(-endpoint,0)+ca.fmax(endpoint-stroke_m,0)
        stop_f = m['stop_stiffness_n_m']*(ca.fmax(-endpoint,0)-ca.fmax(endpoint-stroke_m,0))
        stop_f -= ca.if_else(penetration>0,m['stop_damping_n_s_m']*endpoint_v,0)
        total_force -= stop_f
        total_moment -= sign*half*ca.cos(phi)*stop_f
        contact_heat += ca.if_else(penetration>0,m['stop_damping_n_s_m']*endpoint_v**2,0)
        storage += .5*m['stop_stiffness_n_m']*penetration**2
        drum_pen = ca.fmax(-s,0)+ca.fmax(s-stroke_m,0)
        drum_stop = m['stop_stiffness_n_m']*(ca.fmax(-s,0)-ca.fmax(s-stroke_m,0))
        drum_stop -= ca.if_else(drum_pen>0,m['stop_damping_n_s_m']*vel,0)
        drum_stop_heat = ca.if_else(drum_pen>0,m['stop_damping_n_s_m']*vel**2,0)
        storage += .5*m['stop_stiffness_n_m']*drum_pen**2
        own_fault = live if i==0 else ca.SX(0)
        delay = c['watchdog_s'] if fault in ('torque_frozen','communication_loss') else c['local_detection_s']
        stop_time = tf+delay
        local_stop = (t>=stop_time) if i==0 and fault in ('load_cell_zero','encoder_loss','torque_inverted','torque_frozen') else ca.SX(0)
        if fault=='mains_loss_braked' and i==0:
            local_stop = live
        if fault=='handle_release':
            local_stop = t>=tf+c['local_detection_s']
        if fault in ('emergency_stop','communication_loss'):
            local_stop = live if fault=='emergency_stop' else t>=tf+c['watchdog_s']
        if i==1 and case.get('peer_stop',False) and fault not in ('none','dump_failure','mains_loss_buffered','handle_release'):
            local_stop = t>=stop_time+c['peer_stop_delay_s']
        # Stateful hardware-trip proposal. Zero-crossing events latch this unit;
        # voltage recovery never clears it. Peer policy does not replace local action.
        local_stop = ca.logic_or(local_stop,u['trip_latched']>.5)
        if n==2 and case.get('peer_stop',False):
            other = 4+(1-i)*len(UNIT_FIELDS)
            peer_latched = x[other+UNIT_FIELDS.index('trip_latched')]>.5
            peer_time = x[other+UNIT_FIELDS.index('trip_time_s')]
            local_stop = ca.logic_or(local_stop,ca.logic_and(peer_latched,t>=peer_time+c['peer_stop_delay_s']))
        winding_factor = derate(tw,c['winding_derate_c'],c['winding_stop_c'])
        drive_factor = derate(td,c['drive_derate_c'],c['drive_stop_c'])
        cap_factor = derate(tc,cell['case_max_c']-10,cell['case_max_c'])
        limit = ca.fmin(motor['torque_peak_nm']/motor['kt_nm_per_a'],c['current_limit_a'])*winding_factor*drive_factor*cap_factor
        enabled = ca.logic_not(local_stop)
        margins = ca.vertcat(vb-p['undervoltage_v'],p['trip_v']-vb,
                             c['winding_stop_c']-tw,c['drive_stop_c']-td,cell['case_max_c']-tc)
        event_margins.append(margins)
        command = scales[i]*fr
        if c['end_zone_m'] > 0:
            outer = clamp((s-(stroke_m-c['end_zone_m']))/c['end_zone_m'],0,1)
            inner = clamp((c['end_zone_m']-s)/c['end_zone_m'],0,1)
            command += c['end_zone_gain_n_s_m']*(outer*ca.fmax(u['speed_sensor_m_s'],0)
                                                 -inner*ca.fmax(-u['speed_sensor_m_s'],0))
            command = ca.fmax(command,0)
        if fault=='handle_release':
            command = ca.if_else(t>=tf+c['local_detection_s'],c['rest_tension_n'],command)
        measured = ca.if_else(own_fault,0,u['force_sensor_n']) if fault=='load_cell_zero' else u['force_sensor_n']
        measured_v = ca.if_else(own_fault,0,u['speed_sensor_m_s']) if fault=='encoder_loss' else u['speed_sensor_m_s']
        error = command-measured
        correction = clamp(u['integral_n'],-c['integral_limit_n'],c['integral_limit_n'])
        friction_f = m['friction_n']*friction_scale*ca.tanh(vel/m['friction_speed_m_s'])
        encoder = ca.if_else(own_fault,0,vel) if fault=='encoder_loss' else vel
        measured_a = (encoder-u['speed_sensor_m_s'])/c['encoder_filter_s']
        accel = (1-c['acceleration_blend'])*ar+c['acceleration_blend']*measured_a
        control_f = command+c['kp']*error+correction-friction_f-c['inertia_feedforward']*meq*accel
        control_f -= c['retract_gain_n_s_m']*ca.fmax(-measured_v-c['retract_speed_limit_m_s'],0)
        gear_control = ca.exp(math.log(eta)*ca.tanh(control_f*vel/ref['gear_transition_w']))
        target_tau = control_f*r/g*gear_control
        resistance = (motor['kt_nm_per_a']/(motor['km_nm_per_sqrt_w']*km_scale))**2*(1+.00393*(tw-25))
        emf = motor['kt_nm_per_a']*g*omega
        vmax = drive['modulation_utilization']*ca.fmax(vb,0)
        current_min = ca.fmax(-limit,(emf-vmax)/resistance)
        current_max = ca.fmin(limit,(emf+vmax)/resistance)
        uncontrollable = current_min>current_max
        target_current = ca.if_else(uncontrollable,0,clamp(target_tau/motor['kt_nm_per_a'],current_min,current_max))
        target_tau = motor['kt_nm_per_a']*target_current
        normal_targets.append(target_tau)
        if fault=='torque_inverted':
            target_tau = ca.if_else(own_fault,-target_tau,target_tau)
        if fault=='torque_frozen':
            target_tau = ca.if_else(own_fault,frozen_parameter[i],target_tau)
        # Disabled phases brake through an equivalent external resistance; current may exceed drive ratings.
        brake_current = emf/(resistance+p['phase_brake_resistance_ohm'])
        actual_tau = ca.if_else(enabled,tau,motor['kt_nm_per_a']*brake_current)
        current = actual_tau/motor['kt_nm_per_a']
        copper = current*current*resistance
        brake_heat = ca.if_else(enabled,0,brake_current**2*p['phase_brake_resistance_ohm'])
        gear_torque = g*actual_tau*ca.exp(-math.log(eta)*ca.tanh(g*actual_tau*omega/ref['gear_transition_w']))
        gear_heat = (gear_torque-g*actual_tau)*omega
        friction_heat = friction_f*vel
        motor_bus_power = ca.if_else(enabled,copper-g*actual_tau*omega,0)
        driver_heat = ca.if_else(enabled,p['drive_idle_w']+p['drive_loss_fraction']*ca.fabs(motor_bus_power),
                                p['drive_idle_w']*vb**2/(1+vb**2))
        cap_current = (vc-vb)/cap_r
        cap_esr_heat = cap_current**2*cap_r
        # One-way source; reverse blocking is a required additional hardware function.
        supply_factor = derate(tp,th['supply_derate_start_c'],th['supply_stop_c'])
        source_current = clamp((p['nominal_v']-vb)/p['supply_droop_ohm'],0,
                               supply['power_forced_air_w']/p['nominal_v']*supply_factor)
        if fault.startswith('mains_loss') and i==0:
            source_current = ca.if_else(live,0,source_current)
        source_power = source_current*vb
        supply_heat = source_power*(1/supply['efficiency_nominal']-1)
        wall_input += source_power+supply_heat
        duty = clamp((vb-p['dump_start_v'])/(p['dump_full_v']-p['dump_start_v']),0,1)
        if fault=='dump_failure' and i==0:
            duty = ca.if_else(live,0,duty)
        dump_current = duty*vb/p['dump_resistance_ohm']
        dump_heat = dump_current*vb
        bleed_current = vb/p['bleed_resistance_ohm']
        bleed_heat = bleed_current*vb
        # Protect the mathematical port at zero V; this regularization is an explicit model limit.
        bus_load_current = (motor_bus_power+driver_heat)*vb/(vb*vb+.01)
        port_power = bus_load_current*vb
        regularization_loss = port_power-motor_bus_power-driver_heat
        qwh = (tw-hh)/th['winding_to_housing_k_w']
        qha = (hh-ta)/th['housing_to_air_k_w']
        qda = (td-ta)/th['drive_to_air_k_w']
        qpa = (tp-ta)/th['supply_to_air_k_w']
        qca = (tc-ta)/cap_heat_r
        qra = (tr-ta)/th['dump_to_air_k_w']
        qroom = th['air_to_room_w_k']*(ta-ambient)
        ambient_power += qroom
        dz += [omega,((tension+geometry_force+drum_stop)*r-gear_torque-friction_f*r)/rotor_j,
               (ca.if_else(enabled,target_tau,0)-tau)/c['current_loop_s'],
               ca.if_else(enabled,ca.if_else(ca.fabs(u['integral_n'])<c['integral_limit_n'],c['ki_s']*error,
                          ca.if_else(u['integral_n']*error<0,c['ki_s']*error,0)),0),
               (tension-u['force_sensor_n'])/c['force_filter_s'],
               (vel-u['speed_sensor_m_s'])/c['encoder_filter_s'],
               -cap_current/cap_c,(cap_current+source_current-bus_load_current-dump_current-bleed_current)/p['bus_capacitance_f'],
               (copper-qwh)/th['winding_capacity_j_k'],
               (qwh+gear_heat+friction_heat+drum_stop_heat-qha)/th['housing_capacity_j_k'],
               (driver_heat-qda)/th['drive_capacity_j_k'],(supply_heat-qpa)/th['supply_capacity_j_k'],
               (cap_esr_heat-qca)/cap_heat_c,(dump_heat+brake_heat+bleed_heat-qra)/th['dump_capacity_j_k'],
               (qha+qda+qpa+qca+qra+cable_heat+regularization_loss-qroom)/th['air_capacity_j_k'],0,0,0]
        capacities = (th['winding_capacity_j_k'],th['housing_capacity_j_k'],th['drive_capacity_j_k'],
                      th['supply_capacity_j_k'],cap_heat_c,th['dump_capacity_j_k'],th['air_capacity_j_k'])
        storage += .5*cap_c*vc*vc+.5*p['bus_capacitance_f']*vb*vb
        storage += sum(capacity*(temp-ambient) for capacity,temp in zip(capacities,(tw,hh,td,tp,tc,tr,ta)))
        f0 = scales[i]*lbf_to_n(defaults.rest_tension_lbf)
        s0 = (scenario.start_offset_m-f0*m['routing_length_m']/(m['cable_ea_n']*cable_ea_scale))/(1+f0/(m['cable_ea_n']*cable_ea_scale))
        theta0 = float(np.interp(s0,xb,qb))
        r0 = float(radii[min(np.searchsorted(qb,theta0,side='right')-1,len(radii)-1)])
        geometry0 = .5*f0*f0/(m['cable_ea_n']*cable_ea_scale)
        state0 += [theta0,0,(f0+geometry0)*r0/g,0,f0,0,p['nominal_v'],p['nominal_v']]+[ambient]*7+[0,-1,0]
        initial_margins = [p['nominal_v']-p['undervoltage_v'],p['trip_v']-p['nominal_v'],
                           c['winding_stop_c']-ambient,c['drive_stop_c']-ambient,cell['case_max_c']-ambient]
        if min(initial_margins)<=0:
            base = 4+i*len(UNIT_FIELDS)
            state0[base+UNIT_FIELDS.index('torque_nm')] = 0
            state0[base+UNIT_FIELDS.index('trip_latched')] = 1
            state0[base+UNIT_FIELDS.index('trip_time_s')] = 0
            state0[base+UNIT_FIELDS.index('trip_reason')] = next(j+1 for j,vv in enumerate(initial_margins) if vv<=0)
        for key,value in {'payout_m':s,'radius_m':r,'tension_n':tension,'command_n':command,'endpoint_m':endpoint,
                          'endpoint_speed_m_s':endpoint_v,'motor_current_a':current,'capacitor_current_a':cap_current,
                          'motor_electrical_hz':ca.fabs(g*omega)*motor['pole_pairs']/(2*math.pi),'motor_bus_w':motor_bus_power,'supply_bus_w':source_power,'dump_w':dump_heat,
                          'copper_w':copper,'esr_w':cap_esr_heat,'gear_w':gear_heat,'cable_damping_w':cable_heat,
                          'phase_brake_w':brake_heat,'drive_enabled':enabled,'local_stop':local_stop,
                          'target_torque_nm':target_tau,'voltage_uncontrollable':ca.logic_and(enabled,uncontrollable),'port_regularization_w':regularization_loss}.items():
            observables[f'unit_{i}.{key}'] = value
    dz[1] = (user_force-total_force)/mass
    dz[3] = (user_moment-total_moment)/bar_i if n==2 else 0
    ambient_power += contact_heat
    quad = ca.vertcat(user_force*v+user_moment*w,wall_input,ambient_power)
    ode = ca.vertcat(*dz)
    energy = ca.Function('storage',[x],[storage])
    obs = ca.Function('observables',[t,x,frozen_parameter],[ca.vertcat(*observables.values())])
    dynamics = ca.Function('rhs',[t,x,frozen_parameter],[ode,quad])
    targets = ca.Function('unfrozen_targets',[t,x],[ca.vertcat(*normal_targets)])
    event_index = ca.SX.sym('event_index')
    post_state = ca.SX(x)
    zero = []
    for i,margins in enumerate(event_margins):
        base = 4+i*len(UNIT_FIELDS)
        latched = x[base+UNIT_FIELDS.index('trip_latched')]>.5
        zero.append(ca.if_else(latched,ca.SX.ones(len(TRIP_REASONS)),margins))
        own_event = ca.logic_and(event_index>=i*len(TRIP_REASONS),event_index<(i+1)*len(TRIP_REASONS))
        # Apply simultaneous events together, preserving exact paired symmetry.
        simultaneous = ca.mmin(margins)<=1e-7
        trip = ca.logic_and(ca.logic_not(latched),ca.logic_or(own_event,simultaneous))
        reason = ca.SX(0)
        for j in reversed(range(len(TRIP_REASONS))):
            reason = ca.if_else(margins[j]<=1e-7,j+1,reason)
        reason = ca.if_else(own_event,event_index-i*len(TRIP_REASONS)+1,reason)
        for field,value in [('trip_latched',1),('trip_time_s',t),('trip_reason',reason),
                            ('integral_n',0),('torque_nm',0)]:
            index = base+UNIT_FIELDS.index(field)
            post_state[index] = ca.if_else(trip,value,x[index])
    transition = ca.Function('physical_trip_transition',[event_index,t,x],[post_state])
    return dict(t=t,x=x,p=frozen_parameter,ode=ode,quad=quad,energy=energy,observables=obs,normal_targets=targets,observable_names=list(observables),
                state_names=state_names,state0=np.array(state0),rhs=dynamics,capacitance_f=cap_c,
                esr_ohm=cap_r,rotor_inertia_kg_m2=rotor_j,stroke_m=stroke_m,units=n,
                zero=ca.vertcat(*zero),transition=transition)


def _integrate_segment(name,dae,start,times,options,initial,parameters):
    """CVODES first; use independent BDF event location for its dense-output bug.

    Only CV_ILL_INPUT from experimental event interpolation is eligible. No
    tolerance/step relaxation or equation change is made. Other errors propagate.
    """
    import casadi as ca
    solver=ca.integrator(name,'cvodes',dae,start,times,options)
    try:
        result=solver(x0=initial,p=parameters)
        return np.array(result['xf']),np.array(result['qf']),solver.stats(),{'backend':'CVODES','fallback_reason':None}
    except RuntimeError as error:
        if 'CV_ILL_INPUT' not in str(error):raise
        reason=str(error)
    from scipy.integrate import solve_ivp
    nx=len(initial)
    rhs=ca.Function('bdf_rhs',[dae['t'],dae['x'],dae['p']],[ca.vertcat(dae['ode'],dae['quad'])])
    jac=ca.Function('bdf_jac',[dae['t'],dae['x'],dae['p']],
                    [ca.horzcat(ca.jacobian(ca.vertcat(dae['ode'],dae['quad']),dae['x']),ca.SX.zeros(nx+3,3))])
    zeros=ca.Function('bdf_zeros',[dae['t'],dae['x'],dae['p']],[dae['zero']])
    fun=lambda t,y:np.array(rhs(t,y[:nx],parameters)).ravel()
    derivative=lambda t,y:np.array(jac(t,y[:nx],parameters))
    events=[]
    for index in range(dae['zero'].numel()):
        def event(t,y,index=index):return float(zeros(t,y[:nx],parameters)[index])
        event.terminal=True;event.direction=-1
        events.append(event)
    output=np.empty((nx+3,len(times)));filled=np.zeros(len(times),dtype=bool)
    state=np.concatenate((initial,np.zeros(3)));current=start
    steps,calls=0,0
    for _ in range(options['max_events']+1):
        solution=solve_ivp(fun,(current,float(times[-1])),state,method='BDF',jac=derivative,
                           events=events,dense_output=True,rtol=options['reltol'],atol=options['abstol'],
                           max_step=options['max_step_size'])
        if not solution.success:raise RuntimeError('BDF event fallback failed: '+solution.message)
        steps+=len(solution.t)-1;calls+=solution.nfev
        end=float(solution.t[-1]);mask=(times>=current)&(times<=end)
        # Several distinct trips may fall between adjacent requested samples.
        # SciPy's OdeSolution cannot evaluate an empty time vector.
        if mask.any():
            output[:,mask]=solution.sol(times[mask]);filled[mask]=True
        if solution.status!=1:
            if not filled.all():raise RuntimeError('BDF fallback left missing output points')
            return output[:nx],output[nx:],{'nsteps':steps,'nfevals':calls}, {
                'backend':'SciPy BDF','fallback_reason':reason}
        trigger=next(index for index,values in enumerate(solution.t_events) if len(values))
        state=solution.y[:,-1].copy()
        post=options['transition'](index=trigger,t=end,x=state[:nx],z=[],p=parameters,u=[])['post_x']
        state[:nx]=np.array(post).ravel()
        equal=times==end
        output[:,equal]=state[:,None];filled[equal]=True
        current=end
    raise RuntimeError('BDF fallback exceeded event budget')


def simulate(cfg,parts,scenario,defaults,stroke_m,case,*,maximum_step_s=None,tolerance_scale=1.,model_factory=None,**sensitivity):
    import casadi as ca
    model = (model_factory or build_model)(cfg,parts,scenario,defaults,stroke_m,case,**sensitivity)
    duration = case.get('window_s',scenario_duration_s(scenario,defaults))
    if duration > scenario_duration_s(scenario,defaults)+1e-6:
        raise ConfigError('coupled window exceeds complete scenario duration')
    step = cfg['solver']['output_step_s']
    times = np.unique(np.append(np.arange(0,duration,step),duration))
    # Align known discontinuities with output points, including all fault/coordination times.
    if case['fault']!='none':
        tf = case['fault_time_s']
        extra = [tf,tf+cfg['control']['local_detection_s'],tf+cfg['control']['watchdog_s'],
                 tf+cfg['control']['local_detection_s']+cfg['control']['peer_stop_delay_s'],
                 tf+cfg['control']['watchdog_s']+cfg['control']['peer_stop_delay_s']]
        times = np.unique(np.append(times,[t for t in extra if 0<t<duration]))
    opts = dict(abstol=cfg['solver']['absolute_tolerance']*tolerance_scale,
                reltol=cfg['solver']['relative_tolerance']*tolerance_scale,
                max_num_steps=cfg['solver']['max_steps'],quad_err_con=True,
                max_step_size=maximum_step_s or cfg['solver']['maximum_step_s'])
    # Mean/difference coordinates preserve the exact invariant of a symmetric pair.
    # The physical equations are unchanged. This avoids seeding a free-release
    # instability through round-off in two separately integrated identical states.
    physical_state = lambda values: np.asarray(values)
    initial = model['state0']
    if case['units']==2:
        y = ca.SX.sym('modal_state',len(initial))
        size = len(model.get('unit_fields',UNIT_FIELDS))
        pair = ca.vertcat(y[:4],y[4:4+size]-y[4+size:],y[4:4+size]+y[4+size:])
        rhs = ca.substitute(model['ode'],model['x'],pair)
        quadrature = ca.substitute(model['quad'],model['x'],pair)
        ode = ca.vertcat(rhs[:4],(rhs[4:4+size]+rhs[4+size:])/2,(rhs[4+size:]-rhs[4:4+size])/2)
        dae = dict(t=model['t'],x=y,p=model['p'],ode=ode,quad=quadrature,
                   zero=ca.substitute(model['zero'],model['x'],pair))
        initial = np.concatenate((initial[:4],(initial[4:4+size]+initial[4+size:])/2,
                                  (initial[4+size:]-initial[4:4+size])/2))
        converter = ca.Function('physical_from_modal',[y],[pair])
        physical_state = lambda values: np.array(converter.map(values.shape[1])(values))
        transition_input = y
        event_index = ca.SX.sym('event_index')
        physical_post = model['transition'](event_index,model['t'],pair)
        transition_post = ca.vertcat(physical_post[:4],
                                    (physical_post[4:4+size]+physical_post[4+size:])/2,
                                    (physical_post[4+size:]-physical_post[4:4+size])/2)
    else:
        dae = {k:model[k] for k in ('t','x','p','ode','quad','zero')}
        transition_input = model['x']
        event_index = ca.SX.sym('event_index')
        transition_post = model['transition'](event_index,model['t'],transition_input)
    empty_z,empty_u = ca.SX.sym('z',0),ca.SX.sym('u',0)
    opts['transition'] = ca.Function('latched_trip',
        [event_index,model['t'],transition_input,empty_z,model['p'],empty_u],
        [transition_post,empty_z],ca.event_in(),ca.event_out())
    opts.update(event_tol=1e-9,max_events=10,max_event_iter=100)
    params = np.zeros(case['units'])
    backends=[]
    if case['fault']=='torque_frozen' and case['fault_time_s']>0:
        tf = case['fault_time_s']
        pre_times = times[times<=tf]
        pre_states,pre_works,pre_stats,backend=_integrate_segment('before_freeze',dae,0,pre_times,opts,initial,params)
        backends.append(backend)
        params = np.array(model['normal_targets'](tf-1e-12,physical_state(pre_states)[:,-1])).ravel()
        post_times = times[times>tf]
        post_states,post_works,post_stats,backend=_integrate_segment('after_freeze',dae,tf,post_times,opts,pre_states[:,-1],params)
        backends.append(backend)
        states = np.concatenate((pre_states,post_states),axis=1)
        works = np.concatenate((pre_works,post_works+pre_works[:,-1,None]),axis=1)
        stats = {key:pre_stats.get(key,0)+post_stats.get(key,0) for key in ('nsteps','nfevals')}
    else:
        if case['fault']=='torque_frozen':
            params = np.array(model['normal_targets'](0,model['state0'])).ravel()
        states,works,stats,backend=_integrate_segment('coupled_solver',dae,0,times,opts,initial,params)
        backends.append(backend)
    states = physical_state(states)
    values = np.array(model['observables'].map(len(times))(times.reshape(1,-1),states,
                                                         np.repeat(params[:,None],len(times),axis=1)))
    energy = np.array(model['energy'].map(len(times))(states)).ravel()
    residual = works[0]+works[1]-works[2]-(energy-energy[0])
    signals = dict(t=times,energy_storage_j=energy,energy_residual_j=residual)
    signals.update(zip(model['state_names'],states))
    signals.update(zip(model['observable_names'],values))
    signals.update(zip(QUADRATURES,works))
    metrics = summarize(signals,cfg,parts,case)
    metrics['solver_steps'] = int(stats.get('nsteps',0))
    metrics['solver_rhs_calls'] = int(stats.get('nfevals',0))
    metrics['solver_segments'] = backends
    return dict(metrics=metrics,signals=signals,model=model)


def summarize(sig,cfg,parts,case):
    t = sig['t']
    magnitude = max(float(np.max(np.abs(sig['user_work_j']))+np.max(sig['wall_input_j'])),1.)
    metrics = dict(duration_s=float(t[-1]),energy_residual_max_j=float(np.max(np.abs(sig['energy_residual_j']))),
                   energy_residual_fraction=float(np.max(np.abs(sig['energy_residual_j'])))/magnitude,
                   user_work_j=float(sig['user_work_j'][-1]),wall_input_j=float(sig['wall_input_j'][-1]),
                   ambient_heat_j=float(sig['ambient_heat_j'][-1]),
                   storage_change_j=float(sig['energy_storage_j'][-1]-sig['energy_storage_j'][0]),
                   max_bar_angle_deg=float(np.max(np.abs(sig['bar_angle_rad'])))*180/math.pi,
                   max_bar_displacement_error_m=float(np.max(np.abs(sig['bar_position_m']-sig['reference_position_m']))))
    fault_t = case.get('fault_time_s',t[-1]+1)
    normal = (t>=1)&(t<fault_t)
    if not normal.any(): normal = t<fault_t
    for i in range(case['units']):
        prefix = f'unit_{i}.'
        command,force = sig[prefix+'command_n'],sig[prefix+'tension_n']
        err = force[normal]-command[normal]
        rms = float(np.sqrt(np.mean(err*err))) if err.size else None
        metrics[prefix+'tracking_rms_n'] = rms
        metrics[prefix+'tracking_fraction'] = rms/max(float(np.sqrt(np.mean(command[normal]**2))),2.) if err.size else None
        metrics[prefix+'normal_overshoot_fraction'] = float(np.maximum(err,0).max())/max(float(command[normal].max()),2.) if err.size else None
        metrics[prefix+'max_electrical_hz'] = float(sig[prefix+'motor_electrical_hz'].max())
        metrics[prefix+'port_regularization_max_w'] = float(np.abs(sig[prefix+'port_regularization_w']).max())
        metrics[prefix+'peak_tension_n'] = float(force.max())
        metrics[prefix+'min_bus_v'] = float(sig[prefix+'bus_v'].min())
        metrics[prefix+'max_bus_v'] = float(sig[prefix+'bus_v'].max())
        metrics[prefix+'max_current_a'] = float(np.abs(sig[prefix+'motor_current_a']).max())
        for field in ('winding_c','housing_c','drive_c','supply_c','capacitor_c','dump_c','air_c'):
            metrics[prefix+'max_'+field] = float(sig[prefix+field].max())
        metrics[prefix+'voltage_uncontrollable_fraction'] = float(sig[prefix+'voltage_uncontrollable'].mean())
        metrics[prefix+'min_payout_m'] = float(sig[prefix+'payout_m'].min())
        metrics[prefix+'max_payout_m'] = float(sig[prefix+'payout_m'].max())
        metrics[prefix+'min_tension_n'] = float(force.min())
        metrics[prefix+'peak_endpoint_speed_m_s'] = float(np.abs(sig[prefix+'endpoint_speed_m_s']).max())
        tripped = sig[prefix+'trip_latched']>.5
        metrics[prefix+'trip_latched'] = bool(tripped.any())
        metrics[prefix+'trip_time_s'] = float(sig[prefix+'trip_time_s'][tripped][0]) if tripped.any() else None
        reason = int(round(sig[prefix+'trip_reason'][tripped][0])) if tripped.any() else 0
        metrics[prefix+'trip_reason'] = TRIP_REASONS[reason-1] if reason else None
    metrics['worst_peak_tension_n'] = max(metrics[f'unit_{i}.peak_tension_n'] for i in range(case['units']))
    metrics['worst_winding_c'] = max(metrics[f'unit_{i}.max_winding_c'] for i in range(case['units']))
    metrics['minimum_bus_v'] = min(metrics[f'unit_{i}.min_bus_v'] for i in range(case['units']))
    metrics['maximum_bus_v'] = max(metrics[f'unit_{i}.max_bus_v'] for i in range(case['units']))
    return metrics


def assess_case(metrics,cfg,parts,case,criteria):
    reference=cfg['reference']
    drive=parts[reference['drive']]['values']
    rope=parts[reference['rope']]['values']
    rows=[]
    for i in range(case['units']):
        k=f'unit_{i}.'
        failed=[]
        if case['fault']=='none':
            if metrics[k+'trip_latched']:
                failed.append('latched protective trip during normal operation')
            if metrics[k+'tracking_fraction'] > criteria['tracking_rms_fraction_max']['value']:
                failed.append('proposed tracking RMS')
            if metrics[k+'normal_overshoot_fraction'] > criteria['normal_overshoot_fraction_max']['value']:
                failed.append('proposed normal overshoot')
        if metrics[k+'max_bus_v'] >= drive['voltage_absolute_max_v']:
            failed.append('drive absolute voltage')
        if metrics[k+'min_bus_v'] < cfg['power']['undervoltage_v']:
            failed.append('operating undervoltage')
        if metrics[k+'max_electrical_hz'] > drive['recommended_electrical_frequency_hz']:
            failed.append('recommended electrical frequency')
        if metrics[k+'voltage_uncontrollable_fraction'] > 0:
            failed.append('virtual motor voltage controllability')
        if metrics[k+'max_air_c'] > drive['ambient_max_c_for_ratings']:
            failed.append('drive rated ambient conditions')
        for suffix,maximum in [('winding_c',cfg['control']['winding_stop_c']),
                               ('drive_c',cfg['control']['drive_stop_c']),
                               ('supply_c',cfg['thermal']['supply_stop_c']),
                               ('capacitor_c',parts[reference['capacitor']]['values']['case_max_c'])]:
            if metrics[k+'max_'+suffix] >= maximum:
                failed.append('thermal '+suffix)
        if metrics[k+'peak_tension_n']*criteria['rope_design_factor']['value'] > rope['spliced_breaking_n']:
            failed.append('proposed spliced rope strength factor')
        if metrics[k+'min_payout_m'] < -.001 or metrics[k+'max_payout_m'] > criteria['usable_stroke_m']['value']+.001:
            failed.append('virtual travel stop engagement')
        rows.append({'failed_checks':failed,'qualified':False,
                     'scope':'model comparison; fault force/body-motion acceptance and physical review remain open'})
    return rows


def fingerprint(root):
    """Include actual model code as well as all configuration/reference inputs."""
    root = Path(root)
    _,_,_,base = load_engineering(root)
    h = hashlib.sha256(base.encode())
    for rel in ('configs/coupled.yaml','configs/scenarios.yaml','requirements/engineering.yaml',
                'src/odrt/coupled.py','src/odrt/drivetrain.py','src/odrt/scenarios.py'):
        source = Path(__file__).with_name(Path(rel).name) if rel.startswith('src/') else root/rel
        h.update(rel.encode()+b'\0'+source.read_bytes()+b'\0')
    return h.hexdigest()


def run_study(root=Path('.'),reports=Path('reports'),only=None,verify=False):
    """Regenerate complete case traces and an auditable numerical assessment."""
    import casadi as ca
    import scipy
    from odrt.project import load_inputs
    root,reports = Path(root),Path(reports)
    model_hash_at_start = fingerprint(root)
    inputs = load_inputs(root)
    cfg,parts = load_coupled(root,inputs.scenarios)
    names = {c['name'] for c in cfg['cases']}
    if only and set(only)-names:
        raise ConfigError(f'unknown coupled cases {sorted(set(only)-names)}')
    build = root/'build'/'engineering'
    build.mkdir(parents=True,exist_ok=True)
    reports.mkdir(parents=True,exist_ok=True)
    results = {}
    for case in cfg['cases']:
        if only and case['name'] not in only:
            continue
        print(f'coupled {case["name"]}: starting',flush=True)
        try:
            value = simulate(cfg,parts,inputs.scenarios[case['scenario']],inputs.defaults,
                             inputs.envelope.max_usable_stroke_m,case)
        except RuntimeError as exc:
            results[case['name']] = {'solver_failure':str(exc),'numerical_valid':False}
            print(f'coupled {case["name"]}: solver failed; retained as failed evidence',flush=True)
            continue
        np.savez_compressed(build/f'coupled__{case["name"]}.npz',**value['signals'])
        m = value['metrics']
        m['energy_check_pass'] = m['energy_residual_fraction'] <= load_engineering(root)[0]['energy_residual_fraction_max']['value']
        m['finite_values'] = all(np.isfinite(v).all() for v in value['signals'].values())
        m['numerical_valid'] = m['energy_check_pass'] and m['finite_values']
        m['trace'] = f'build/engineering/coupled__{case["name"]}.npz'
        m['unit_assessment'] = assess_case(m,cfg,parts,case,load_engineering(root)[0])
        results[case['name']] = m
        print(f'coupled {case["name"]}: {m["duration_s"]:.1f}s; energy residual {m["energy_residual_fraction"]:.3g}; '
              f'bar rotation {m["max_bar_angle_deg"]:.2f} degrees',flush=True)
    verification = verify_study(inputs,cfg,parts,build) if verify else None
    if fingerprint(root) != model_hash_at_start:
        raise ConfigError('coupled model or inputs changed during run; results were not published')
    result = {'input_hash':model_hash_at_start,'casadi_version':ca.__version__,'numpy_version':np.__version__,
              'scipy_version':scipy.__version__,
              'case_scope':'partial' if only else 'complete configured suite',
              'configured_cases':len(cfg['cases']),'completed_cases':len(results),'cases':results,
              'verification':verification,'assessment':'REVISE','hardware_qualified':False,
              'reference':cfg['reference'],'power':cfg['power'],'model_limits':MODEL_LIMITS}
    name = 'coupled_partial' if only else 'coupled'
    (reports/f'{name}.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    if not only:
        plot_results(build,reports)
    write_report(result,cfg,parts,reports/f'{name}.md')
    return result


def verify_study(inputs,cfg,parts,build):
    """Independent resolution and physical-parameter perturbation comparisons."""
    criteria = load_engineering(inputs.root)[0]
    refinements = {}
    selected = ('single_heavy_full','single_low_full','left_power_loss_coordinated','paired_release','paired_release_asymmetric')
    for name in selected:
        case = next(c for c in cfg['cases'] if c['name']==name)
        records = []
        for factor in (1,2,4):
            print(f'coupled convergence {name}: refinement {factor}',flush=True)
            r = simulate(cfg,parts,inputs.scenarios[case['scenario']],inputs.defaults,
                         inputs.envelope.max_usable_stroke_m,case,
                         maximum_step_s=cfg['solver']['maximum_step_s']/factor,tolerance_scale=1/factor**2)
            np.savez_compressed(build/f'convergence__{name}__{factor}.npz',**r['signals'])
            records.append(r['metrics'])
        keys = ['unit_0.peak_tension_n','unit_0.min_bus_v','unit_0.max_bus_v','unit_0.max_winding_c',
                'max_bar_angle_deg','max_bar_displacement_error_m','unit_0.tracking_rms_n']
        floors = {'max_bar_angle_deg':.1,'max_bar_displacement_error_m':.001,'unit_0.tracking_rms_n':2}
        changes = {}
        for key in keys:
            a,b,c = (m[key] for m in records)
            denom = max(abs(c),floors.get(key,1e-3))
            changes[key] = {'coarse_to_medium_fraction':abs(b-a)/denom,'medium_to_fine_fraction':abs(c-b)/denom}
        limit = criteria['convergence_normal_fraction_max' if case['fault']=='none' else 'convergence_fault_fraction_max']['value']
        refinements[name] = {'maximum_steps_s':[cfg['solver']['maximum_step_s']/f for f in (1,2,4)],
                             'relative_tolerances':[cfg['solver']['relative_tolerance']/f**2 for f in (1,2,4)],
                             'metrics':records,'changes':changes,'criterion_fraction':limit,
                             'pass':all(v['medium_to_fine_fraction']<=limit for v in changes.values())}
    perturbations = {
        'nominal':{},'km_low':{'km_scale':.34/.53},'esr_end_life':{'esr_scale':2},
        'capacitance_end_life':{'capacitance_scale':.8},'combined_cell_aging':{'esr_scale':2,'capacitance_scale':.8},
        'soft_rope':{'cable_ea_scale':.5},'stiff_rope':{'cable_ea_scale':2},
        'inertia_high':{'inertia_scale':1.5},'friction_high':{'friction_scale':2},
        'warm_room':{'ambient_offset_c':15},'soft_user':{'user_stiffness_scale':.5},
        'stiff_user':{'user_stiffness_scale':2},'low_user_damping':{'user_damping_scale':.5},
    }
    sensitivity = {}
    case = next(c for c in cfg['cases'] if c['name']=='paired_heavy_full')
    for name,params in perturbations.items():
        print(f'coupled sensitivity {name}',flush=True)
        r = simulate(cfg,parts,inputs.scenarios[case['scenario']],inputs.defaults,
                     inputs.envelope.max_usable_stroke_m,case,**params)
        np.savez_compressed(build/f'sensitivity__{name}.npz',**r['signals'])
        sensitivity[name] = {'parameters':params,'metrics':r['metrics']}
    verified = all(v['pass'] for v in refinements.values()) and all(
        v['metrics']['energy_residual_fraction'] <= criteria['energy_residual_fraction_max']['value']
        for v in sensitivity.values())
    return {'pass':verified,'refinement':refinements,'sensitivity':sensitivity,
            'energy_criterion_fraction':criteria['energy_residual_fraction_max']['value'],
            'scope':'Two-unit reference with stated parameter proposals; no hardware validation inferred'}


MODEL_LIMITS = [
    'Reference hardware does not yet meet the complete owner package envelope; the model is a reusable reference plant, not a feasible product claim.',
    'Virtual DC-equivalent Kt/current/voltage conventions need calibration to phase/RMS/FOC data. Published modulation is a conservative model bound.',
    'Winding/housing and driver/supply/enclosure thermal paths are explicit proposals. Cell ESR and thermal characteristics are sourced; airflow, assembly and derating need validation.',
    'Level-wind/guided routing is proposed. Winding radius crossovers are idealized steps; cable mass, transverse motion, friction hysteresis and bend-fatigue damage are not resolved.',
    'Cable stiffness changes with free length; the associated spring-energy gradient is included. Damping heat is accounted explicitly.',
    'The paired solver uses mean/difference coordinates to preserve exact symmetry; physical asymmetry is injected explicitly. Bar model uses parallel cable directions, rigid geometry and an impedance-controlled user. It is not a validated human model, especially for large rotations or a release.',
    'Fault detection, peer-stop latency and phase-brake topology are idealized proposals. Local stop is independent of peer reaction; there is no certified STO or validated communication protocol.',
    'Travel stops are virtual springs/dampers. A real arrestor, adapter, retention joint and substrate must still be designed and reviewed.',
    'Voltage and winding/drive/cell overtemperature crossings latch the unit off through solver events. No automatic rearm exists within a scenario; explicit restart requires a new run. Detection is ideal and instantaneous at the thresholds; hardware delay, contact switching and an authorized reset protocol remain unvalidated. CasADi event support is experimental.',
    'CVODES event-interpolation CV_ILL_INPUT failures are retried with SciPy BDF event location using the same equations, coordinates, quadratures and tolerances. Every fallback is recorded per solver segment. Other failures propagate; no tolerance relaxation is used.',
    'The motor bus port is regularized near zero volts. This correction is logged and is negligible only while the bus remains in the declared operating range.',
    'Energy conservation verifies internal accounting, not the truth of component parameters or completeness of physical effects.',
]


def write_report(result,cfg,parts,path):
    lines = ['# Coupled open resistance-control reference', '',
             '> Simulation only. This is a reusable electromechanical model with explicit limitations, not hardware or human-use qualification.', '',
             f'Input/model hash: `{result["input_hash"]}`', '',
             f'Case scope: **{result["case_scope"]}**; {result["completed_cases"]} of {result["configured_cases"]} configured cases. '
             f'CasADi {result["casadi_version"]}, NumPy {result["numpy_version"]}.', '',
             '## Physical and software contracts', '',
             'Positive displacement is cable payout; positive motor torque resists payout. Each unit has separate supply, '
             'bulk capacitance, DC-link capacitance and ESR. A two-unit rigid bar has translation and rotation, so a '
             'one-sided fault can move the bar asymmetrically. Sensor filters, PI control, current/voltage saturation, '
             'thermal derating, regeneration, dump resistance, local braking and optional peer stops operate in one coupled ODE.', '',
             'Motor, housing, drive, supply, capacitor bank, dump and enclosure air each have thermal storage. '
             'The energy ledger integrates user work and wall input against mechanical/elastic/electrical/thermal storage '
             'and heat leaving to the room. Neither negative gear losses nor a hidden voltage clamp is permitted.', '',
             'The reference uses a RO100 Lite, 6:1 reduction, 30 mm core and a 6-turn, two-layer 5 mm rope drum. '
             'The bank is 22 series 350 F cells: 15.91 F and 0.0704 Ω initial ESR, not an ideal 2 F bank. '
             'A 3 mF separate DC-link state resolves capacitor-to-bus current and voltage drop. '
             'The EPP-500-48 candidate is modeled with required forced cooling and one-way output blocking.', '',
             'Power-loss, stuck sensing, frozen/inverted commands, communication loss, release and dump failure are '
             'injected as named scenarios. Protective detection delays are assumptions; results compare policies and '
             'do not validate a detector or establish a safe release. Voltage and winding/drive/cell temperature '
             'crossings latch a unit off through solver zero-crossing events. A recovering bus cannot rearm it; '
             'a fresh simulation run initializes the latch. Where configured, the peer stops after the trip '
             'time plus the assumed peer delay. Event transitions reset only controller/discrete states, '
             'with no instantaneous change to stored physical energy.', '',
             '## Case results', '',
             '| Case | Duration s | Tracking RMS % (unit 0) | Worst tension lbf | Worst bus min / max V | Worst winding °C | Bar rotation ° | Energy residual fraction |',
             '|---|---:|---:|---:|---|---:|---:|---:|']
    for name,m in result['cases'].items():
        if 'solver_failure' in m:
            lines.append(f'| {name} | **SOLVER FAILURE** | — | — | — | — | — | — |')
            continue
        tracking = 100*m['unit_0.tracking_fraction'] if m['unit_0.tracking_fraction'] is not None else float('nan')
        lines.append(f'| {name} | {m["duration_s"]:.1f} | {tracking:.2f} | {m["worst_peak_tension_n"]/lbf_to_n(1):.1f} | '
                     f'{m["minimum_bus_v"]:.2f} / {m["maximum_bus_v"]:.2f} | {m["worst_winding_c"]:.1f} | '
                     f'{m["max_bar_angle_deg"]:.2f} | {m["energy_residual_fraction"]:.3g} |')
    lines += ['', '## Latched protective events', '',
              'Bus extrema in the case table are sampled values; a trip record locates the threshold crossing '
              'between samples. Hardware sensing delay, switching overshoot and reset authorization are not modeled.', '',
              '| Case | Unit | Trip reason | Event time s |', '|---|---:|---|---:|']
    for name,m in result['cases'].items():
        for unit in range(2):
            prefix=f'unit_{unit}.'
            if m.get(prefix+'trip_latched'):
                lines.append(f'| {name} | {unit} | {m[prefix+"trip_reason"]} | {m[prefix+"trip_time_s"]:.6f} |')
    lines += ['', '## Explicit design-screen outcomes', '',
              'These outcomes compare the model to documented or proposed criteria; none is human-use qualification.', '',
              '| Case | Failed model/design criteria |', '|---|---|']
    for name,m in result['cases'].items():
        if 'unit_assessment' not in m:
            continue
        failures = [f'unit {i}: '+', '.join(v['failed_checks']) for i,v in enumerate(m['unit_assessment']) if v['failed_checks']]
        lines.append(f'| {name} | '+('; '.join(failures) or 'No listed screen failure; hardware and model limitations remain')+' |')
    verification = result['verification']
    if result['case_scope']=='complete configured suite':
        lines += ['', '![Heavy-set coupled states](figures/coupled_heavy.png)', '',
                  '![Paired power-loss comparison](figures/coupled_peer_fault.png)', '',
                  '![Endurance derating](figures/coupled_endurance.png)']
    if verification:
        lines += ['', '## Resolution refinement', '',
                  'Refinement tightens both the maximum internal time step and integration tolerance; output sample spacing '
                  'is unchanged. The table compares medium and fine resolutions using absolute floors for near-zero metrics.', '',
                  '| Case | Maximum medium-to-fine change | Criterion | Outcome |', '|---|---:|---:|---|']
        for name,r in verification['refinement'].items():
            maximum = max(v['medium_to_fine_fraction'] for v in r['changes'].values())
            lines.append(f'| {name} | {maximum:.3%} | {r["criterion_fraction"]:.1%} | {"pass" if r["pass"] else "FAIL / unresolved"} |')
        lines += ['', '## Parameter uncertainty', '',
                  '| Perturbation | Paired tracking RMS % (unit 0) | Winding max °C | Min bus V | Energy residual fraction |',
                  '|---|---:|---:|---:|---:|']
        for name,r in verification['sensitivity'].items():
            m = r['metrics']
            lines.append(f'| {name} | {100*m["unit_0.tracking_fraction"]:.2f} | {m["unit_0.max_winding_c"]:.1f} | '
                         f'{m["unit_0.min_bus_v"]:.2f} | {m["energy_residual_fraction"]:.3g} |')
    else:
        lines += ['', '**Resolution/sensitivity verification was not requested for this run.** Do not infer convergence from energy balance alone.']
    lines += ['', '## Limits and qualification gaps', '']+['- '+s for s in MODEL_LIMITS]
    lines += ['', '## Reproduction and extension', '',
              '`make coupled` runs all configured cases. `make coupled-verify` adds resolution and sensitivity comparisons. '
              '`odrt coupled --only CASE ...` writes separate partial reports so a subset cannot masquerade as a complete suite. '
              'Named traces live under `build/engineering/`; `reports/coupled.json` contains the auditable metrics. '
              'Configuration is in `configs/coupled.yaml`; component data is separate in `data/engineering_components.yaml`. '
              'Independent tests check storage gradients, conservation, symmetry, ESR current/heat and fault behavior.', '',
              '**Assessment: REVISE.** Supported operation is limited to cases with acceptable tracking, ratings, '
              'energy and refinement evidence. The complete compact package, reviewed electrical/mechanical design '
              'and controlled component/hardware measurements remain required. The eight-item engineering goal remains active.', '']
    path.write_text('\n'.join(lines))


def plot_results(build,reports):
    """Scientific plots from the saved states; no additional simulated geometry."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figures=reports/'figures'
    figures.mkdir(parents=True,exist_ok=True)
    with np.load(build/'coupled__single_heavy_full.npz') as s:
        t=s['t']
        fig,axes=plt.subplots(4,1,figsize=(10,9),sharex=True,layout='constrained')
        axes[0].plot(t,s['unit_0.command_n']/lbf_to_n(1),label='command',color='#555555',linestyle='--')
        axes[0].plot(t,s['unit_0.tension_n']/lbf_to_n(1),label='actual',color='#2f6b85')
        axes[0].set_ylabel('Cable force (lbf)')
        axes[1].plot(t,s['unit_0.capacitor_v'],label='internal bank voltage',color='#697946')
        axes[1].plot(t,s['unit_0.bus_v'],label='drive bus voltage',color='#a06136')
        axes[1].set_ylabel('Voltage (V)')
        for field,label,color in (('motor_bus_w','motor bus','#2f6b85'),('supply_bus_w','supply','#697946'),('esr_w','ESR heat','#a06136')):
            axes[2].plot(t,s['unit_0.'+field],label=label,color=color)
        axes[2].set_ylabel('Power (W)')
        for field,label,color in (('winding_c','winding','#a06136'),('drive_c','drive','#2f6b85'),('capacitor_c','bank','#697946')):
            axes[3].plot(t,s['unit_0.'+field],label=label,color=color)
        axes[3].set_ylabel('Temperature (°C)');axes[3].set_xlabel('Time (s)')
        fig.suptitle('Coupled reference: complete 250 lbf heavy set — simulation assumptions apply')
        for ax in axes:
            ax.grid(alpha=.2);ax.legend(fontsize=8,loc='upper right')
        fig.savefig(figures/'coupled_heavy.png',dpi=140,metadata={'Software':None});plt.close(fig)
    fig,axes=plt.subplots(3,2,figsize=(12,8),sharex=True,layout='constrained')
    for col,(name,title) in enumerate((('left_power_loss_uncoordinated','Local braking; peer continues'),
                                     ('left_power_loss_coordinated','Local braking and proposed peer stop'))):
        with np.load(build/f'coupled__{name}.npz') as s:
            t=s['t']
            axes[0,col].set_title(title)
            axes[0,col].plot(t,np.rad2deg(s['bar_angle_rad']),color='#a06136',label='bar rotation')
            for unit,color in ((0,'#2f6b85'),(1,'#697946')):
                axes[1,col].plot(t,s[f'unit_{unit}.tension_n']/lbf_to_n(1),color=color,label=f'unit {unit}')
                axes[2,col].plot(t,s[f'unit_{unit}.endpoint_m'],color=color,label=f'endpoint {unit}')
            for ax in axes[:,col]:
                ax.axvline(2.6,color='#999999',linestyle='--',linewidth=.8)
                ax.grid(alpha=.2);ax.legend(fontsize=8)
            axes[2,col].set_xlabel('Time (s)')
    for ax,label in zip(axes[:,0],('Angle (degrees)','Cable force (lbf)','Endpoint payout (m)')):
        ax.set_ylabel(label)
    fig.suptitle('Paired bar: one-sided mains loss — user and detection models are unvalidated')
    fig.savefig(figures/'coupled_peer_fault.png',dpi=140,metadata={'Software':None});plt.close(fig)
    with np.load(build/'coupled__single_endurance_full.npz') as s:
        t=s['t'];fig,axes=plt.subplots(2,1,figsize=(10,6),sharex=True,layout='constrained')
        axes[0].plot(t,s['unit_0.command_n']/lbf_to_n(1),label='command',color='#777777',linestyle='--')
        axes[0].plot(t,s['unit_0.tension_n']/lbf_to_n(1),label='actual',color='#2f6b85')
        axes[0].set_ylabel('Cable force (lbf)')
        axes[1].plot(t,s['unit_0.winding_c'],label='winding',color='#a06136')
        axes[1].plot(t,s['unit_0.drive_c'],label='drive',color='#2f6b85')
        axes[1].plot(t,s['unit_0.air_c'],label='air',color='#697946')
        axes[1].set_ylabel('Temperature (°C)');axes[1].set_xlabel('Time (s)')
        fig.suptitle('Complete endurance profile: thermal derating reduces delivered resistance')
        for ax in axes:ax.grid(alpha=.2);ax.legend(fontsize=8)
        fig.savefig(figures/'coupled_endurance.png',dpi=140,metadata={'Software':None});plt.close(fig)
