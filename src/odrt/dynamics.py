"""Time-domain cable/drum/controller/bus model with fault injection.

Coordinates: s = cable paid out at the drum, x_h = handle position (both m,
payout positive). Unstretched cable means x_h == s; stretch e = x_h - s.

  Cable    F = k(s) e + c de/dt for e > 0, else 0 (a cable cannot push)
  Drum     m_eq s'' = F - F_drive - F_fric(s')          m_eq = J_eq / r^2
  Motors   tau' = (tau_cmd - tau) / T_c, |tau_cmd| <= n * peak torque
  Gearbox  F_drive = tau G / r * eta^(-tanh(s'/v_eps))  (A-009 sign rule, smoothed)
  Handle   kinematic (follows the scenario) until released, then m_h x_h'' = -F
  Bus      d(C V^2 / 2)/dt = P_supply - P_motors - P_dump; the supply cannot sink

Controller: tension feedforward + PI on the (delayed, noisy) load cell, optional
friction feedforward. Safety layer (proposals, A-017): retraction speed limiter
and load-cell/model disagreement monitor that falls back to feedforward.
Simulation only: none of this is a validated safety function (R-09).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from odrt.config import ConfigError, check_keys, integer, load_yaml, number, string
from odrt.drivetrain import km_hot
from odrt.scenarios import Trajectory

FAULTS = ("none", "handle_release", "load_cell_zero", "power_loss_open", "power_loss_shorted",
          "no_dump_resistor", "torque_frozen", "torque_inverted", "encoder_loss", "deck_empty",
          "power_loss_braked")


@dataclass(frozen=True)
class Case:
    name: str
    scenario: str
    window_s: float
    fault: str
    fault_time_s: float
    safety: bool
    independent: bool = True   # independent safety channel: watchdog + plausibility -> STO with phase short


@dataclass(frozen=True)
class DynParams:
    designs: tuple
    dt_s: float
    ea_n: float
    routing_length_m: float
    damping_ratio: float
    friction_n: float
    friction_v_eps: float
    current_tc_s: float
    handle_mass_kg: float
    user_mass_kg: float
    user_k: float
    user_b: float
    handle_end_stop_m: float
    lc_delay_s: float
    lc_noise_n: float
    enc_delay_s: float
    seed: int
    kp: float
    ki_per_s: float
    integral_limit_n: float
    friction_ff: bool
    inertia_comp: float
    accel_filter_s: float
    accel_clip: float
    max_retract_speed: float
    retract_gain: float
    disagreement_n: float
    disagreement_time_s: float
    release_fraction: float
    release_time_s: float
    rest_tension_n: float
    release_accel_fraction: float
    sto_brake_n_s_per_m: float
    reverse_drive_n: float
    sensor_fault_ramp_s: float
    watchdog_s: float
    payout_fault_speed: float
    payout_fault_time_s: float
    bus_v: float
    bus_c: float
    supply_max_w: float
    undervoltage_v: float
    overvoltage_v: float
    dump_on_v: float
    dump_r: float
    cases: tuple


def load_dynamics(path: Path, options: dict, scenarios: dict) -> DynParams:
    d = load_yaml(path)
    w = str(path)
    check_keys(d, w, ["designs", "dt_s", "cable", "friction_at_cable_n", "friction_smoothing_m_s",
                      "current_loop_time_constant_s", "handle_mass_kg", "user", "handle_end_stop_m", "sensors",
                      "controller", "safety", "independent", "bus", "cases"])
    if not isinstance(d["designs"], list) or not d["designs"]:
        raise ConfigError(f"{w}.designs: must be a non-empty list")
    for name in d["designs"]:
        if name not in options:
            raise ConfigError(f"{w}.designs: unknown option {name!r}")
        if options[name].component.kind != "motor" or options[name].component.km() is None:
            raise ConfigError(f"{w}.designs: {name!r} lacks motor data (Km) needed for dynamics")
    c, s, k, sf, b, u = d["cable"], d["sensors"], d["controller"], d["safety"], d["bus"], d["user"]
    check_keys(u, f"{w}.user", ["mass_kg", "stiffness_n_per_m", "damping_n_s_per_m"])
    check_keys(c, f"{w}.cable", ["axial_stiffness_ea_n", "routing_length_m", "damping_ratio"])
    check_keys(s, f"{w}.sensors", ["load_cell_delay_s", "load_cell_noise_n", "encoder_delay_s", "seed"])
    check_keys(k, f"{w}.controller", ["kp", "ki_per_s", "integral_limit_n", "friction_feedforward",
                                       "inertia_compensation", "accel_filter_s", "accel_clip_m_s2"])
    check_keys(sf, f"{w}.safety", ["max_retract_speed_m_s", "retract_speed_gain_n_per_m_s", "disagreement_n",
                                   "disagreement_time_s", "release_fraction", "release_time_s", "rest_tension_n",
                                   "release_accel_fraction", "sensor_fault_ramp_s"])
    ind = d["independent"]
    check_keys(ind, f"{w}.independent", ["watchdog_s", "payout_fault_speed_m_s", "payout_fault_time_s",
                                         "reverse_drive_n", "brake_n_s_per_m"])
    check_keys(b, f"{w}.bus", ["nominal_v", "capacitance_f", "supply_max_w", "undervoltage_v", "overvoltage_v", "dump_on_v",
                               "dump_resistor_ohm"])
    pos = dict(minimum=0, exclusive_minimum=True)
    nonneg = dict(minimum=0)
    if not isinstance(k["friction_feedforward"], bool):
        raise ConfigError(f"{w}.controller.friction_feedforward: expected true/false")
    cases = []
    if not isinstance(d["cases"], list) or not d["cases"]:
        raise ConfigError(f"{w}.cases: must be a non-empty list")
    names = set()
    for i, raw in enumerate(d["cases"]):
        cw = f"{w}.cases[{i}]"
        check_keys(raw, cw, ["name", "scenario", "window_s", "fault"], ["fault_time_s", "safety", "independent"])
        name = string(raw["name"], f"{cw}.name")
        if name in names:
            raise ConfigError(f"{cw}.name: duplicate {name!r}")
        names.add(name)
        if raw["scenario"] not in scenarios:
            raise ConfigError(f"{cw}.scenario: unknown scenario {raw['scenario']!r}")
        if raw["fault"] not in FAULTS:
            raise ConfigError(f"{cw}.fault: {raw['fault']!r} not in {FAULTS}")
        if raw["fault"] != "none" and "fault_time_s" not in raw:
            raise ConfigError(f"{cw}: fault_time_s required for fault {raw['fault']!r}")
        safety = raw.get("safety", True)
        independent = raw.get("independent", True)
        if not isinstance(safety, bool) or not isinstance(independent, bool):
            raise ConfigError(f"{cw}: safety and independent must be true/false")
        window = number(raw["window_s"], f"{cw}.window_s", **pos)
        cases.append(Case(name, raw["scenario"], window, raw["fault"],
                          number(raw.get("fault_time_s", 0.0), f"{cw}.fault_time_s", minimum=0, maximum=window),
                          safety, independent))
    p = DynParams(
        designs=tuple(d["designs"]), dt_s=number(d["dt_s"], f"{w}.dt_s", **pos),
        ea_n=number(c["axial_stiffness_ea_n"], f"{w}.cable.axial_stiffness_ea_n", **pos),
        routing_length_m=number(c["routing_length_m"], f"{w}.cable.routing_length_m", **pos),
        damping_ratio=number(c["damping_ratio"], f"{w}.cable.damping_ratio", **nonneg),
        friction_n=number(d["friction_at_cable_n"], f"{w}.friction_at_cable_n", **nonneg),
        friction_v_eps=number(d["friction_smoothing_m_s"], f"{w}.friction_smoothing_m_s", **pos),
        current_tc_s=number(d["current_loop_time_constant_s"], f"{w}.current_loop_time_constant_s", **pos),
        handle_mass_kg=number(d["handle_mass_kg"], f"{w}.handle_mass_kg", **pos),
        user_mass_kg=number(u["mass_kg"], f"{w}.user.mass_kg", **pos),
        user_k=number(u["stiffness_n_per_m"], f"{w}.user.stiffness_n_per_m", **nonneg),
        user_b=number(u["damping_n_s_per_m"], f"{w}.user.damping_n_s_per_m", **nonneg),
        handle_end_stop_m=number(d["handle_end_stop_m"], f"{w}.handle_end_stop_m", **nonneg),
        lc_delay_s=number(s["load_cell_delay_s"], f"{w}.sensors.load_cell_delay_s", **nonneg),
        lc_noise_n=number(s["load_cell_noise_n"], f"{w}.sensors.load_cell_noise_n", **nonneg),
        enc_delay_s=number(s["encoder_delay_s"], f"{w}.sensors.encoder_delay_s", **nonneg),
        seed=integer(s["seed"], f"{w}.sensors.seed", minimum=0),
        kp=number(k["kp"], f"{w}.controller.kp", **nonneg),
        ki_per_s=number(k["ki_per_s"], f"{w}.controller.ki_per_s", **nonneg),
        integral_limit_n=number(k["integral_limit_n"], f"{w}.controller.integral_limit_n", **nonneg),
        friction_ff=k["friction_feedforward"],
        inertia_comp=number(k["inertia_compensation"], f"{w}.controller.inertia_compensation", minimum=0, maximum=1.5),
        accel_filter_s=number(k["accel_filter_s"], f"{w}.controller.accel_filter_s", **pos),
        accel_clip=number(k["accel_clip_m_s2"], f"{w}.controller.accel_clip_m_s2", **pos),
        max_retract_speed=number(sf["max_retract_speed_m_s"], f"{w}.safety.max_retract_speed_m_s", **pos),
        retract_gain=number(sf["retract_speed_gain_n_per_m_s"], f"{w}.safety.retract_speed_gain_n_per_m_s",
                            **nonneg),
        disagreement_n=number(sf["disagreement_n"], f"{w}.safety.disagreement_n", **pos),
        disagreement_time_s=number(sf["disagreement_time_s"], f"{w}.safety.disagreement_time_s", **nonneg),
        release_fraction=number(sf["release_fraction"], f"{w}.safety.release_fraction", minimum=0, maximum=1),
        release_time_s=number(sf["release_time_s"], f"{w}.safety.release_time_s", **nonneg),
        rest_tension_n=number(sf["rest_tension_n"], f"{w}.safety.rest_tension_n", **nonneg),
        release_accel_fraction=number(sf["release_accel_fraction"], f"{w}.safety.release_accel_fraction",
                                      minimum=0, exclusive_minimum=True, maximum=1),
        reverse_drive_n=number(ind["reverse_drive_n"], f"{w}.independent.reverse_drive_n", **pos),
        sto_brake_n_s_per_m=number(ind["brake_n_s_per_m"], f"{w}.independent.brake_n_s_per_m", **pos),
        sensor_fault_ramp_s=number(sf["sensor_fault_ramp_s"], f"{w}.safety.sensor_fault_ramp_s", **pos),
        watchdog_s=number(ind["watchdog_s"], f"{w}.independent.watchdog_s", **pos),
        payout_fault_speed=number(ind["payout_fault_speed_m_s"], f"{w}.independent.payout_fault_speed_m_s", **pos),
        payout_fault_time_s=number(ind["payout_fault_time_s"], f"{w}.independent.payout_fault_time_s", **pos),
        bus_v=number(b["nominal_v"], f"{w}.bus.nominal_v", **pos),
        bus_c=number(b["capacitance_f"], f"{w}.bus.capacitance_f", **pos),
        supply_max_w=number(b["supply_max_w"], f"{w}.bus.supply_max_w", **pos),
        undervoltage_v=number(b["undervoltage_v"], f"{w}.bus.undervoltage_v", **pos),
        overvoltage_v=number(b["overvoltage_v"], f"{w}.bus.overvoltage_v", **pos),
        dump_on_v=number(b["dump_on_v"], f"{w}.bus.dump_on_v", **pos),
        dump_r=number(b["dump_resistor_ohm"], f"{w}.bus.dump_resistor_ohm", **pos),
        cases=tuple(cases),
    )
    if not p.undervoltage_v < p.bus_v < p.dump_on_v < p.overvoltage_v:
        raise ConfigError(f"{w}.bus: need undervoltage_v < nominal_v < dump_on_v < overvoltage_v")
    return p


@dataclass(frozen=True)
class Plant:
    count: int
    gear_ratio: float
    efficiency: float
    radius_m: float
    m_eq_kg: float
    peak_torque_per_motor_nm: float
    km_hot: float

    @classmethod
    def from_option(cls, opt, common):
        arch = opt.architecture
        r = arch.drum_core_radius_m + common.cable_diameter_m / 2
        return cls(count=opt.count, gear_ratio=arch.gear_ratio, efficiency=arch.gear_efficiency, radius_m=r,
                   m_eq_kg=arch.inertia_at_drum() / r**2,
                   peak_torque_per_motor_nm=opt.component.peak_torque_nm,
                   km_hot=km_hot(arch, common) / math.sqrt(opt.count))  # per-motor Km


def _interp(traj: Trajectory, t):
    return (np.interp(t, traj.t, traj.x), np.interp(t, traj.t, traj.v), np.interp(t, traj.t, traj.a),
            np.interp(t, traj.t, traj.tension_n))


def run(case: Case, traj: Trajectory, plant: Plant, p: DynParams) -> dict:
    """Simulate one case; returns decimated signals plus summary metrics."""
    dt = p.dt_s
    n = int(round(case.window_s / dt)) + 1
    t = np.arange(n) * dt
    x_ref, v_ref, a_ref, f_cmd = _interp(traj, t)
    rng = np.random.default_rng(p.seed)
    noise = rng.normal(0.0, p.lc_noise_n, n) if p.lc_noise_n > 0 else np.zeros(n)
    lc_lag = int(round(p.lc_delay_s / dt))
    enc_lag = int(round(p.enc_delay_s / dt))

    G, r, eta = plant.gear_ratio, plant.radius_m, plant.efficiency
    m_eq = plant.m_eq_kg
    tau_max = plant.count * plant.peak_torque_per_motor_nm
    torque_to_force = G / r                 # total motor torque -> drum force (before efficiency)
    fault_on = case.fault != "none"
    fault_idx = int(round(case.fault_time_s / dt)) if fault_on else n + 1

    # initial state: stationary, cable pre-stretched to the commanded tension
    x_h = x_ref[0]
    k0 = p.ea_n / (p.routing_length_m + x_h)
    s = x_h - f_cmd[0] / k0
    v_s = 0.0
    v_h = 0.0
    tau = f_cmd[0] / torque_to_force
    integ = 0.0
    released = False
    fallback = False
    disagree_t = 0.0
    e_bus = 0.5 * p.bus_c * p.bus_v**2
    hit_speed = None
    v_meas_prev = 0.0
    release_latched = False
    low_t = 0.0
    sensor_fault = False
    sensor_fault_t0 = 0.0
    sensor_fault_f0 = 0.0
    sto = False
    sto_t = None
    frozen_tau = None
    payout_t = 0.0
    a_meas = 0.0

    F_hist = np.zeros(n)
    s_hist = np.zeros(n)
    v_hist = np.zeros(n)
    xh_hist = np.zeros(n)
    vh_hist = np.zeros(n)
    tau_hist = np.zeros(n)
    vbus_hist = np.zeros(n)
    fmeas_hist = np.zeros(n)

    km2 = plant.km_hot**2
    for i in range(n):
        # --- cable tension
        e = x_h - s
        k = p.ea_n / (p.routing_length_m + max(s, 0.0))
        m_hand = p.handle_mass_kg if released else p.handle_mass_kg + p.user_mass_kg
        c = 2 * p.damping_ratio * math.sqrt(k * m_eq * m_hand / (m_eq + m_hand))
        F = k * e + c * (v_h - v_s) if e > 0 else 0.0
        if F < 0:
            F = 0.0
        F_hist[i] = F

        # --- sensors (delayed)
        j = i - lc_lag
        f_meas = (F_hist[j] if j >= 0 else F_hist[0]) + noise[i]
        if fault_on and case.fault == "load_cell_zero" and i >= fault_idx:
            f_meas = 0.0
        fmeas_hist[i] = f_meas
        je = i - enc_lag
        v_meas = v_hist[je] if je >= 0 else 0.0
        if fault_on and case.fault == "encoder_loss" and i >= fault_idx:
            v_meas = 0.0  # encoder stuck: speed reads zero
        a_meas += ((v_meas - v_meas_prev) / dt - a_meas) * dt / p.accel_filter_s
        v_meas_prev = v_meas

        # --- controller: drum force command
        target = f_cmd[i]
        deck_empty = fault_on and case.fault == "deck_empty" and i >= fault_idx
        if case.safety:
            if deck_empty:  # presence sensing: only rest tension with nobody on the deck (H-14)
                target = p.rest_tension_n
            # Fault policy (A-017): low measured tension WITH the drum accelerating inward is a release
            # (the motor torque is suddenly unopposed); low tension WITHOUT that is a sensor fault.
            if (not release_latched and not sensor_fault and f_meas < p.release_fraction * target
                    and target > 4 * p.rest_tension_n):
                low_t += dt
                if low_t >= p.release_time_s:
                    # unopposed drive accelerates the drum inward at ~ target / m_eq after a release
                    if a_meas < -p.release_accel_fraction * target / m_eq:
                        release_latched = True
                    else:
                        sensor_fault, sensor_fault_t0, sensor_fault_f0 = True, t[i], target
                        fallback = True
                        integ = 0.0
            elif not release_latched and not sensor_fault:
                low_t = 0.0
            if release_latched:
                target = p.rest_tension_n
                integ = 0.0
            elif sensor_fault:  # keep the load on feedforward and ramp it down instead of dropping it
                frac = max(0.0, 1.0 - (t[i] - sensor_fault_t0) / p.sensor_fault_ramp_s)
                target = p.rest_tension_n + (sensor_fault_f0 - p.rest_tension_n) * frac
        err = target - f_meas
        f_drive_cmd = target
        if not fallback:
            integ = min(max(integ + p.ki_per_s * err * dt, -p.integral_limit_n), p.integral_limit_n)
            f_drive_cmd += p.kp * err + integ
        if p.friction_ff:
            f_drive_cmd -= p.friction_n * math.tanh(v_meas / p.friction_v_eps)
        a_ff = min(max(a_meas, -p.accel_clip), p.accel_clip)
        f_drive_cmd -= p.inertia_comp * m_eq * a_ff  # hide drum inertia from the user
        if case.safety:
            if v_meas < -p.max_retract_speed:  # retracting too fast: brake by pushing payout
                f_drive_cmd -= p.retract_gain * (-v_meas - p.max_retract_speed)
            # model tension: drivetrain force + drum inertia + friction (A-017)
            f_est = (tau * torque_to_force * eta ** (-math.tanh(v_meas / p.friction_v_eps)) + m_eq * a_meas
                     + p.friction_n * math.tanh(v_meas / p.friction_v_eps))
            if abs(f_meas - f_est) > p.disagreement_n:
                disagree_t += dt
                if disagree_t >= p.disagreement_time_s:
                    fallback = True
                    integ = 0.0
            else:
                disagree_t = 0.0
        tau_cmd = min(max(f_drive_cmd / torque_to_force, -tau_max), tau_max)
        if math.sqrt(2 * e_bus / p.bus_c) < p.undervoltage_v:
            tau_cmd = 0.0  # drive undervoltage lockout
        if fault_on and i >= fault_idx:
            if case.fault == "torque_frozen":  # controller hang: the drive keeps the last current command
                if frozen_tau is None:
                    frozen_tau = tau_cmd
                tau_cmd = frozen_tau
            elif case.fault == "torque_inverted":  # sign error: drive pushes the cable out
                tau_cmd = -tau_cmd
        # Independent channel (separate MCU, own sensing; proposal A-017): a watchdog on a hung controller
        # and a payout-with-low-tension plausibility check both trip STO with the phases shorted.
        if case.independent and not sto:
            if fault_on and case.fault == "torque_frozen" and i >= fault_idx and t[i] - case.fault_time_s >= p.watchdog_s:
                sto = True
            # wrong-sign check: the motor is driving cable OUT (measured current) while the drum pays out fast
            # AND tension well below the target (inertia compensation also drives outward, but keeps tension
            # near target). Needs independent tension sensing plus the target from the main controller.
            if (v_s > p.payout_fault_speed and tau * torque_to_force < -p.reverse_drive_n
                    and F < 0.5 * f_cmd[i] and f_cmd[i] > 4 * p.rest_tension_n):
                payout_t += dt
                if payout_t >= p.payout_fault_time_s:
                    sto = True
            else:
                payout_t = 0.0
            if sto:
                sto_t = t[i]

        # --- actuator
        if fault_on and case.fault == "power_loss_open" and i >= fault_idx:
            tau += (0.0 - tau) * dt / p.current_tc_s
        elif fault_on and case.fault == "power_loss_shorted" and i >= fault_idx:
            # phases shorted: braking torque Km^2 * omega per motor (inductance neglected: upper bound)
            tau = plant.count * km2 * (G * v_s / r)
        elif sto or (fault_on and case.fault == "power_loss_braked" and i >= fault_idx):
            # STO / power-loss relay shorts the phases through braking resistors: drum force = c * v,
            # capped at the shorted-phase value (resistors can only weaken the short).
            c_short = plant.count * km2 * (G / r) ** 2
            tau = min(p.sto_brake_n_s_per_m, c_short) * v_s / torque_to_force
        else:
            tau += (tau_cmd - tau) * dt / p.current_tc_s
        tau_hist[i] = tau

        eff = eta ** (-math.tanh(v_s / p.friction_v_eps))
        f_drive = tau * torque_to_force * eff
        f_fric = p.friction_n * math.tanh(v_s / p.friction_v_eps)

        # --- bus energy (per-motor copper loss; supply cannot sink)
        omega_m = G * v_s / r
        powered = not (fault_on and case.fault.startswith("power_loss") and i >= fault_idx) and not sto
        if powered:
            p_motor = plant.count * (tau / plant.count) ** 2 / km2 - tau * omega_m
            dump = not (fault_on and case.fault == "no_dump_resistor" and i >= fault_idx)
            e_try = e_bus - p_motor * dt
            # the chopper switches at the threshold, so decide on the predicted voltage
            if dump and math.sqrt(2 * max(e_try, 0.0) / p.bus_c) > p.dump_on_v:
                # exact update of dE/dt = -P_motor - 2E/(R C): the RC constant is near dt
                rc = p.dump_r * p.bus_c
                e_inf = -p_motor * rc / 2
                e_bus = e_inf + (e_bus - e_inf) * math.exp(-2 * dt / rc)
            else:
                e_bus = e_try
            e_nom = 0.5 * p.bus_c * p.bus_v**2
            if e_bus < e_nom:  # supply tops the bus up, within its power limit
                e_bus = min(e_nom, e_bus + p.supply_max_w * dt)
            e_bus = max(e_bus, 1e-9)
        vbus_hist[i] = math.sqrt(2 * e_bus / p.bus_c)

        # --- integrate (semi-implicit Euler)
        a_s = (F - f_drive - f_fric) / m_eq
        v_s += a_s * dt
        s += v_s * dt
        if fault_on and case.fault == "handle_release" and i >= fault_idx:
            released = True
        if released:
            f_user = 0.0
        else:  # user anticipates the set tension and tracks the planned path through arm impedance
            expected = p.rest_tension_n if (fault_on and case.fault == "deck_empty") else f_cmd[i]  # casual pull
            f_user = (expected + p.user_k * (x_ref[i] - x_h) + p.user_b * (v_ref[i] - v_h)
                      + (p.user_mass_kg + p.handle_mass_kg) * a_ref[i])
        if x_h > p.handle_end_stop_m or v_h > 0 or not released:
            v_h += (f_user - F) / m_hand * dt
            x_h += v_h * dt
            if released and x_h <= p.handle_end_stop_m:
                if hit_speed is None:
                    hit_speed = -v_h
                x_h, v_h = p.handle_end_stop_m, 0.0
        s_hist[i], v_hist[i], xh_hist[i], vh_hist[i] = s, v_s, x_h, v_h

    after = t >= case.fault_time_s if fault_on else np.ones(n, dtype=bool)
    tracking = slice(int(round(1.0 / dt)), n) if not fault_on else slice(0, max(fault_idx, 1))
    err = F_hist[tracking] - f_cmd[tracking]
    over_v = np.flatnonzero((vbus_hist > p.overvoltage_v) & after)
    metrics = {
        "peak_tension_lbf": float(np.max(F_hist) / 4.4482216152605),
        "peak_tension_after_fault_lbf": float(np.max(F_hist[after]) / 4.4482216152605),
        "tracking_rms_error_n": float(np.sqrt(np.mean(err**2))) if err.size else None,
        "tracking_rms_error_pct": (float(100 * np.sqrt(np.mean(err**2)) / max(np.mean(f_cmd[tracking]), 1e-9))
                                   if err.size else None),
        "peak_retract_speed_m_s": float(max(0.0, -np.min(np.minimum(v_hist[after], vh_hist[after])))),
        "handle_end_stop_speed_m_s": hit_speed,
        "peak_bus_v": float(np.max(vbus_hist)),
        "time_to_overvoltage_ms": (float((t[over_v[0]] - case.fault_time_s) * 1e3) if over_v.size else None),
        "torque_saturated_fraction": float(np.mean(np.abs(tau_hist) >= tau_max * 0.999)),
        "fell_back_to_feedforward": fallback,
        "release_detected": release_latched,
        "sensor_fault_detected": sensor_fault,
        "sto_tripped": sto,
        "sto_after_fault_ms": (float((sto_t - case.fault_time_s) * 1e3) if sto_t is not None and fault_on else None),
        "min_bus_v": float(np.min(vbus_hist)),
        "peak_hand_deviation_after_fault_m": (float(np.max(np.abs(xh_hist[after] - x_ref[after])))
                                              if fault_on and case.fault not in ("handle_release", "deck_empty")
                                              else None),
        "tension_below_10pct_ms": _time_below(F_hist, f_cmd, after, t, case.fault_time_s) if fault_on else None,
    }
    step = max(1, int(round(0.002 / dt)))
    signals = {"t": t[::step], "f_cmd": f_cmd[::step], "f": F_hist[::step], "f_meas": fmeas_hist[::step],
               "v_drum": v_hist[::step], "v_handle": vh_hist[::step], "x_handle": xh_hist[::step],
               "v_bus": vbus_hist[::step]}
    return {"metrics": metrics, "signals": signals}


def _time_below(F, f_cmd, after, t, t0):
    """ms after the fault until tension first drops below 10 % of the command at the fault."""
    idx = np.flatnonzero(after)
    if not idx.size:
        return None
    ref = f_cmd[idx[0]]
    below = idx[F[idx] < 0.1 * ref]
    return float((t[below[0]] - t0) * 1e3) if below.size else None
