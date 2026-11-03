"""Engineering goal inputs, component compatibility and compact architecture screen.

This is a reproducible rejection/shortlisting calculation. Optimistic mechanical
space claims and comparison rating checks cannot establish a feasible product.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
from pathlib import Path

from odrt.config import ConfigError, check_keys, integer, load_yaml, number, string
from odrt.drivetrain import Architecture, Common, Drum
from odrt.units import lbf_to_n

FILES = ('requirements/engineering.yaml', 'data/engineering_components.yaml', 'configs/engineering.yaml')
CRITERIA = ('force_peak_lbf', 'units', 'usable_stroke_m', 'peak_heavy_speed_m_s', 'unit_volume_l_max',
            'unit_length_mm_max', 'unit_width_mm_max', 'unit_height_mm_max', 'unit_mass_kg_max',
            'tracking_rms_fraction_max', 'tracking_absolute_floor_n', 'normal_overshoot_fraction_max',
            'rope_design_factor', 'fatigue_cycles_target', 'energy_residual_fraction_max',
            'convergence_normal_fraction_max', 'convergence_fault_fraction_max', 'retail_per_unit_usd',
            'mount_deflection_mm_max', 'acoustic_db_a_at_1m_max')
STUDY_KEYS = ('motors', 'ropes', 'core_radii_mm', 'turns_per_layer', 'layers', 'ratios', 'routings', 'layouts',
              'dead_turns', 'fleet_angle_deg', 'gear_efficiency', 'drum_inertia_kg_m2',
              'driver_current_screen_a', 'lowest_bus_for_speed_screen_v', 'running_clearance_mm',
              'axial_bearing_pair_mm', 'axial_structure_mm', 'pulley_face_mm', 'drum_flange_pair_mm',
              'flange_radius_extra_mm', 'guided_lead_mm', 'cable_ea_n', 'handle_mass_kg', 'km_sensitivity',
              'reference_snap_lbf', 'capacitor_series')


def load_engineering(root=Path('.')):
    root = Path(root)
    raw = load_yaml(root / FILES[0])
    check_keys(raw, FILES[0], ['criteria'])
    check_keys(raw['criteria'], 'criteria', CRITERIA)
    criteria = raw['criteria']
    for key, spec in criteria.items():
        check_keys(spec, f'criteria.{key}', ['value', 'origin', 'basis', 'method'])
        number(spec['value'], key, minimum=0, exclusive_minimum=True)
        if spec['origin'] not in ('owner', 'provisional', 'verification'):
            raise ConfigError(f'{key}.origin: expected owner/provisional/verification')
        string(spec['basis'], key + '.basis')
        string(spec['method'], key + '.method')
    components = load_yaml(root / FILES[1])
    check_keys(components, FILES[1], ['components'])
    components = components['components']
    if not isinstance(components, dict) or not components:
        raise ConfigError('components: expected a nonempty mapping')
    for key, part in components.items():
        check_keys(part, key, ['role', 'source', 'accessed', 'values', 'availability', 'price_usd', 'notes'])
        if not string(part['source'], key).startswith('https://'):
            raise ConfigError(f'{key}: an https source is required')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(part['accessed'])):
            raise ConfigError(f'{key}: accessed must be YYYY-MM-DD')
        for field in ('role', 'availability', 'notes'):
            string(part[field], key + '.' + field)
        if not isinstance(part['values'], dict) or not part['values']:
            raise ConfigError(f'{key}.values: expected a nonempty mapping')
        for field, value in part['values'].items():
            number(value, f'{key}.{field}', minimum=0, exclusive_minimum=True)
        if part['price_usd'] is not None:
            raise ConfigError(f'{key}: price requires a separately sourced cost record; keep unknown here')
    config = load_yaml(root / FILES[2])
    check_keys(config, FILES[2], ['study'])
    study = config['study']
    check_keys(study, 'study', STUDY_KEYS)
    for key in ('motors', 'ropes'):
        if not isinstance(study[key], list) or not study[key]:
            raise ConfigError(f'study.{key}: expected nonempty list')
        for name in study[key]:
            if name not in components or components[name]['role'] != ('motor' if key == 'motors' else 'rope'):
                raise ConfigError(f'study.{key}: unknown or wrong-role component {name}')
    for key, choices in (('routings', ('unguided', 'guided')),
                         ('layouts', ('legacy_side_mount_5m', 'folded_3m'))):
        if not isinstance(study[key], list) or not study[key] or any(x not in choices for x in study[key]):
            raise ConfigError(f'study.{key}: must be a nonempty subset of {choices}')
    list_fields = ('core_radii_mm', 'turns_per_layer', 'layers', 'ratios', 'km_sensitivity')
    for key in list_fields:
        if not isinstance(study[key], list) or not study[key]:
            raise ConfigError(f'study.{key}: expected nonempty list')
        for value in study[key]:
            number(value, key, minimum=0, exclusive_minimum=True)
            if key in ('turns_per_layer', 'layers'):
                integer(value, key, minimum=1)
    excluded = set(list_fields) | {'motors', 'ropes', 'routings', 'layouts', 'dead_turns'}
    for key in set(study) - excluded:
        number(study[key], key, minimum=0, exclusive_minimum=True)
    integer(study['dead_turns'], 'dead_turns', minimum=0)
    integer(study['capacitor_series'], 'capacitor_series', minimum=1)
    if study['fleet_angle_deg'] > 15 or study['gear_efficiency'] > 1:
        raise ConfigError('fleet angle or efficiency out of range')
    digest = hashlib.sha256()
    for rel in FILES:
        digest.update(rel.encode() + b'\0' + (root / rel).read_bytes() + b'\0')
    # Findings must change when the legacy reference bus is changed.
    digest.update((root / 'configs/dynamics.yaml').read_bytes())
    digest.update(Path(__file__).read_bytes())
    return criteria, components, study, digest.hexdigest()


def fits_envelope(dimensions_mm, limits_mm):
    """Allow rigid orientation changes; every axis must fit, not just volume."""
    return all(a <= b + 1e-9 for a, b in zip(sorted(dimensions_mm), sorted(limits_mm)))


def compatibility_issues(bus, drive):
    issues = []
    maximum = drive['voltage_absolute_max_v']
    for key in ('nominal_v', 'dump_on_v', 'overvoltage_v'):
        if bus[key] >= maximum:
            issues.append(f'{key} {bus[key]:g} V reaches/exceeds drive maximum {maximum:g} V')
    if not bus['nominal_v'] < bus['dump_on_v'] < bus['overvoltage_v']:
        issues.append('require nominal < dump < overvoltage threshold')
    return issues


def candidate(criteria, parts, cfg, motor_id, rope_id, core_mm, turns, layers, ratio, routing, layout):
    motor = parts[motor_id]['values']
    rope = parts[rope_id]['values']
    drive = parts['odrive_s1']['values']
    diameter = rope['diameter_mm']
    common = Common(diameter / 1000, cfg['dead_turns'], 25, 60)
    arch = Architecture('screen', 'analytical architecture screen', ratio, cfg['gear_efficiency'] if ratio > 1 else .98,
                        core_mm / 1000, turns, layers, cfg['drum_inertia_kg_m2'], motor['inertia_kg_m2'],
                        motor['km_nm_per_sqrt_w'])
    drum = Drum(arch, common)
    stroke = criteria['usable_stroke_m']['value']
    capacity = float(drum.capacity[-1] - drum.dead_length_m)
    # Use only occupied layers, not hypothetical empty outer layers.
    rmin = float(drum.radius(stroke, stroke))
    rmax = float(drum.radius(0, stroke))
    force = lbf_to_n(criteria['force_peak_lbf']['value'])
    torque = force * rmax / (ratio * arch.gear_efficiency)
    current = torque / motor['kt_nm_per_a']
    rpm = ratio * criteria['peak_heavy_speed_m_s']['value'] / rmin * 60 / (2 * math.pi)
    speed_upper_rpm = min(motor['rated_rpm'],
                          drive['recommended_electrical_frequency_hz'] * 60 / motor['pole_pairs'],
                          motor['no_load_rpm_at_48v'] * cfg['lowest_bus_for_speed_screen_v'] / 48 *
                          drive['modulation_utilization'])
    inertia = arch.inertia_at_drum() / rmin**2
    flange_d = 2 * (rmax * 1000 + diameter / 2 + cfg['flange_radius_extra_mm'])
    pitch = 3 if layout == 'folded_3m' else 5
    wheel_d = 15 * ratio * pitch / math.pi if ratio > 1 else 0
    pinion_d = 15 * pitch / math.pi
    clearance = cfg['running_clearance_mm']
    if ratio == 1:
        axial = (turns * diameter + cfg['drum_flange_pair_mm'] + cfg['axial_bearing_pair_mm'] +
                 cfg['axial_structure_mm'] + motor['length_mm'])
        radial = max(flange_d, motor['diameter_mm'])
        dims = (radial + 2 * clearance, radial + 2 * clearance, axial + 2 * clearance)
    else:
        centres = max((wheel_d + pinion_d) / 2 + 12, motor['diameter_mm'] / 2 + 10)
        radial_length = max(wheel_d, flange_d) / 2 + centres + motor['diameter_mm'] / 2
        radial_width = max(wheel_d, flange_d, motor['diameter_mm'])
        drum_stack = (turns * diameter + cfg['drum_flange_pair_mm'] + cfg['axial_bearing_pair_mm'] +
                      cfg['axial_structure_mm'] + cfg['pulley_face_mm'])
        axial = max(drum_stack, motor['length_mm'] + cfg['pulley_face_mm'] + cfg['axial_structure_mm'])
        if layout == 'legacy_side_mount_5m':
            axial += motor['length_mm'] + 25
        dims = (radial_length + 2 * clearance, radial_width + 2 * clearance, axial + 2 * clearance)
    fleet = turns * diameter / 2 / math.tan(math.radians(cfg['fleet_angle_deg']))
    lead = fleet if routing == 'unguided' else cfg['guided_lead_mm']
    dims = (dims[0] + lead + flange_d / 2, dims[1], dims[2])
    limits = [criteria[k]['value'] for k in ('unit_length_mm_max', 'unit_width_mm_max', 'unit_height_mm_max')]
    mech_volume = math.prod(dims) / 1e6
    strain_energy = force**2 * (lead / 1000 + stroke) / (2 * cfg['cable_ea_n'])
    rotation_energy = .5 * inertia * criteria['peak_heavy_speed_m_s']['value']**2
    required_mbs = cfg['reference_snap_lbf'] * lbf_to_n(1) * criteria['rope_design_factor']['value']
    failures = []
    if capacity < stroke:
        failures.append('stroke capacity')
    if torque > motor['torque_peak_nm']:
        failures.append('motor peak torque')
    if current > cfg['driver_current_screen_a']:
        failures.append('40 A current screen')
    if rpm > speed_upper_rpm:
        failures.append('conservative speed ceiling')
    if not fits_envelope(dims, limits):
        failures.append('mechanism-only envelope')
    if rope['spliced_breaking_n'] < required_mbs:
        failures.append('reference transient rope strength')
    return dict(motor=motor_id, rope=rope_id, core_mm=core_mm, turns=turns, layers=layers, ratio=ratio,
                routing=routing, layout=layout, usable_capacity_m=capacity, radius_min_mm=rmin*1000,
                radius_max_mm=rmax*1000, radius_variation_fraction=rmax/rmin-1,
                drum_width_mm=turns*diameter, lead_mm=lead, minimum_unguided_lead_mm=fleet,
                mechanism_dimensions_mm=dims, mechanism_volume_l=mech_volume,
                motor_torque_at_peak_nm=torque, motor_current_at_peak_a=current,
                motor_rpm_required=rpm, conservative_speed_upper_rpm=speed_upper_rpm,
                effective_mass_kg=inertia, drum_d_over_rope_min=2*rmin*1000/diameter,
                copper_nominal_w=(torque / motor['km_nm_per_sqrt_w'])**2,
                copper_low_km_w=(torque / min(cfg['km_sensitivity']))**2,
                elastic_energy_j=strain_energy, reflected_kinetic_energy_j=rotation_energy,
                hypothetical_handle_speed_from_stored_energy_m_s=math.sqrt(2*(strain_energy+rotation_energy)/cfg['handle_mass_kg']),
                spliced_strength_n=rope['spliced_breaking_n'], required_strength_n=required_mbs,
                failures=failures, screen_checks_pass=not failures,
                qualification='UNQUALIFIED: full packaging, belt/guide ratings, bend fatigue and coupled dynamics pending')


def run_architecture_study(root=Path('.'), out=Path('reports')):
    root, out = Path(root), Path(out)
    criteria, parts, cfg, fingerprint = load_engineering(root)
    axes = [cfg[k] for k in ('motors', 'ropes', 'core_radii_mm', 'turns_per_layer', 'layers', 'ratios', 'routings', 'layouts')]
    rows = [candidate(criteria, parts, cfg, *values) for values in itertools.product(*axes)]
    eligible = [r for r in rows if r['usable_capacity_m'] >= criteria['usable_stroke_m']['value']]
    survivors = [r for r in eligible if r['screen_checks_pass']]
    counts = {failure: sum(failure in r['failures'] for r in rows) for failure in sorted({f for r in rows for f in r['failures']})}
    bus = load_yaml(root / 'configs/dynamics.yaml')['bus']
    issues = compatibility_issues(bus, parts['odrive_s1']['values'])
    result = dict(input_hash=fingerprint, candidates=rows, failure_counts=counts,
                  screen_checks_pass_count=len(survivors), legacy_bus_issues=issues,
                  assessment='REVISE', physical_qualification=False)
    out.mkdir(parents=True, exist_ok=True)
    results_dir = root / 'build' / 'engineering'
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir/'architecture_screen.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    summary = {key: value for key, value in result.items() if key != 'candidates'}
    summary['candidate_count'] = len(rows)
    summary['sufficient_capacity_count'] = len(eligible)
    summary['full_results'] = 'build/engineering/architecture_screen.json'
    (out/'architecture_screen.json').write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
    write_requirements(criteria, fingerprint, out)
    write_component_review(parts, cfg, issues, fingerprint, out)
    lines = ['# Compact architecture screen', '', '> Analytical rejection and conditional shortlisting only; simulation-only.', '',
             f'Input hash: `{fingerprint}`', '',
             'Owner envelope: **323 × 139 × 100 mm (4.4897 L)** or smaller per unit (ADR-003). '
             'All three dimensions must fit under one rigid orientation. The earlier 20 L placeholder is superseded.', '',
             f'Evaluated {len(rows)} combinations; {len(eligible)} have enough ideal winding capacity; '
             f'**{len(survivors)} pass the listed comparison checks**. No candidate is physically qualified. Conservative screens are assumption-dependent rejections, not proofs of physical impossibility.', '',
             '| Rejection reason | Candidates |', '|---|---:|']
    lines += [f'| {reason} | {count} |' for reason, count in counts.items()]
    lines += ['', '## Method and limits', '',
              '- Compare direct drive, legacy side-mounted 5 mm-pitch belt and folded 3 mm-pitch belt arrangements '
              'with the same force, stroke and speed requirements. All reductions use the same documented motor candidates. '
              'A high-ratio single-stage belt is included and can be rejected on dimensions; no imaginary compact gearbox is assumed.',
              '- Layered winding includes dead turns and only occupied layers. Fleet lead uses half drum width / tan(4°). '
              'A guided path uses a proposed 90 mm lead; the guide/level-wind must still be designed and qualified.',
              '- Folded geometry is an analyst stack-up proposal. Dimensions are **mechanism-only space claims** '
              'including declared bearing/structure/clearance allowances. Electronics, supply, buffer, isolation, cooling '
              'and service access still need an actual combined layout. A small mechanism is not a small complete product.',
              '- Speed screen uses the lowest proposed bus voltage and a conservative 78% utilization factor, capped by '
              'the vendor rated speed and the S1 recommended electrical frequency. No-load-voltage conventions and loaded '
              'curves need validation; passing this comparison screen does not establish a torque-speed operating point.',
              '- Current demand uses published Kt with its stated/uncertain convention. 40 A is the heat-spreader comparison '
              'screen; voltage-dependent peak current is not assumed to be 80 A at 48 V.',
              '- Torque, inertia and copper loss use the worst occupied winding radius where relevant. '
              'Copper loss is reported both at the published Km and the lower uncertainty case; actual coupled temperature matters.',
              '- The 932 lbf legacy snap result is a conservative reference load, not a prediction for every candidate. '
              'It must be replaced by each candidate’s converged transient result. A factor of five on spliced strength '
              'is only the retained comparison screen; it does not qualify shock/human-interactive duty.',
              '- D/d, elastic energy and rotor kinetic energy are reported; no bend-fatigue lifetime is claimed. '
              'The energy-to-handle-speed value is a worst-case energy-transfer illustration, not a transient simulation.', '',
              '## Best dimensional screens', '',
              'Ranked among sufficient-capacity candidates by fewest failed comparison checks, then mechanism volume. '
              'Every row still lacks full electronics packaging and physical qualification.', '',
              '| Motor / rope | Layout / routing | G | Core / turns / layers | Mechanism mm | L | Effective kg | Torque Nm | A | RPM need / ceiling | Failed comparison checks |',
              '|---|---|---:|---|---|---:|---:|---:|---:|---|---|']
    ranked = sorted(eligible, key=lambda r:(len(r['failures']),r['mechanism_volume_l']))
    for r in ranked[:20]:
        dims = ' × '.join(f'{v:.0f}' for v in r['mechanism_dimensions_mm'])
        lines.append(f'| {r["motor"]} / {r["rope"]} | {r["layout"]} / {r["routing"]} | {r["ratio"]} | '
                     f'{r["core_mm"]} / {r["turns"]} / {r["layers"]} | {dims} | {r["mechanism_volume_l"]:.2f} | '
                     f'{r["effective_mass_kg"]:.1f} | {r["motor_torque_at_peak_nm"]:.1f} | '
                     f'{r["motor_current_at_peak_a"]:.0f} | {r["motor_rpm_required"]:.0f} / '
                     f'{r["conservative_speed_upper_rpm"]:.0f} | {", ".join(r["failures"]) or "none (conditional only)"} |')
    lines += ['', '## Decision', '',
              '**REVISE.** The published VOLTRA envelope is an owner requirement. The existing 104 L package is rejected. '
              'Use the machine-readable sweep to identify which torque, speed, winding, routing and package assumptions '
              'must change. Do not select a candidate from low volume alone. The next steps are coupled candidate dynamics, '
              'real belt/guide/fatigue checks and a complete co-located electrical/mechanical layout.', '']
    (out/'architecture_screen.md').write_text('\n'.join(lines))
    return result


def write_requirements(criteria, fingerprint, out):
    lines = ['# Measurable engineering criteria', '', f'Input hash: `{fingerprint}`', '',
             'Owner decisions, proposed design screens and numerical verification criteria remain distinct. '
             'Provisional force/error/structural thresholds are not approved human-use safety limits.', '',
             '| Criterion | Value (units in ID) | Origin | Basis | Acceptance evidence |', '|---|---:|---|---|---|']
    for key, spec in criteria.items():
        lines.append(f'| {key} | {spec["value"]} | {spec["origin"]} | {spec["basis"]} | {spec["method"]} |')
    lines += ['', 'Duty-cycle definitions remain versioned in `configs/scenarios.yaml`: the complete heavy set, '
              '3 s top holds, slow pulls and endurance session must be evaluated, not just a short representative window. '
              'Mounting must cover board, wall and rack load paths, arbitrary pull direction and asymmetry; a door '
              'adapter has no established capacity. Mains operation and independent local safety follow ADR-002. '
              'Noise, life and perceptual smoothness cannot be closed by software-only evidence.', '']
    (out/'engineering_requirements.md').write_text('\n'.join(lines))


def write_component_review(parts, cfg, issues, fingerprint, out):
    lines = ['# Component rating review', '', f'Input hash: `{fingerprint}`', '',
             'Manufacturer-authored sources rechecked 2026-11-02. Exact SKU stock/lead time and fresh quotes are unknown '
             'unless explicitly stated. Values are in `data/engineering_components.yaml`.', '',
             '## Legacy bus incompatibility', '']
    lines += ['- '+issue for issue in issues] or ['No threshold conflict found by the static compatibility check. '
                                                'Dynamic overshoot, margins and hardware protection still require assessment.']
    lines += ['', 'S1 maximum DC voltage is 50.5 V. A simulated bus above that rating fails component compatibility '
              'even if it stays below the old model’s 60 V threshold. The 78% published modulation utilization '
              'and voltage-dependent peak-current curve also constrain the usable envelope.', '',
              '## Candidates and unresolved selection', '', '| Candidate | Status / unresolved question | Source |', '|---|---|---|']
    for key, part in parts.items():
        lines.append(f'| {key} | {part["availability"]}. {part["notes"]} | [manufacturer source]({part["source"]}) |')
    cell = parts['bcap0350_e270_t11']['values']
    n = cfg['capacitor_series']
    lines += ['', '## Supply and buffer consequences', '',
              'The EPP-500-48 candidate occupies 127 × 76.2 × 40 mm, but its 499.2 W rating requires 25 CFM; '
              'natural-convection output is 321.6 W, with input/temperature derating still applicable. '
              'A fan, isolation boundary and airflow path consume additional space.', '',
              f'{n} × 350 F cells in series yield **{cell["capacitance_f"]/n:.2f} F**, '
              f'**{n*cell["esr_initial_max_ohm"]:.4f} Ω** initial ESR, '
              f'and **{n*cell["mass_kg"]:.2f} kg** of cells. '
              f'The end-life screen is {cell["capacitance_f"]*cell["capacitance_end_life_fraction"]/n:.2f} F '
              f'and {n*cell["esr_initial_max_ohm"]*cell["esr_end_life_multiplier"]:.4f} Ω. '
              'The old combination of a 2 F model and large-cell package was not an exact selected bank. '
              'Balancing, pre-charge, discharge, reverse-current blocking and fault protection are additional parts.', '',
              'The new catalog reduces variant ambiguity through primary sources but does not settle measurement conventions, '
              'mounting thermal paths, fatigue, live inventory, pricing or qualification. No candidate is certified for this application.', '']
    (out/'component_review.md').write_text('\n'.join(lines))
