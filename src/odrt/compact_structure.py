"""Load-path screening tied to the compact CAD and candidate dynamic envelope.

This rejects inadequate analytical surrogates; it cannot qualify joints, fatigue,
mounts or a real product. Load corners intentionally combine uncorrelated maxima.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

from odrt.compact_candidate import candidate_fingerprint
from odrt.compact_package import build
from odrt.config import ConfigError,load_yaml
from odrt.coupled import load_coupled
from odrt.engineering import load_engineering
from odrt.units import lbf_to_n


def bearing_reactions(centres,loads):
    """Forces on rotor at two ideal radial supports; z in mm and forces in N."""
    z1,z2=centres
    if z2<=z1:raise ValueError('bearing centres must increase')
    force=sum((np.asarray(f,dtype=float) for z,f in loads),start=np.zeros(2))
    moment=sum(((z-z1)*np.asarray(f,dtype=float) for z,f in loads),start=np.zeros(2))
    upper=-moment/(z2-z1);lower=-force-upper
    residual_force=lower+upper+force
    residual_moment=upper*(z2-z1)+moment
    return lower,upper,float(np.linalg.norm(residual_force)),float(np.linalg.norm(residual_moment))


def shaft_stress(moment_nmm,torque_nmm,diameter_mm):
    bending=32*abs(moment_nmm)/(math.pi*diameter_mm**3)
    shear=16*abs(torque_nmm)/(math.pi*diameter_mm**3)
    return math.sqrt(bending*bending+3*shear*shear)


def generate(root=Path('.')):
    root=Path(root);source=root/'reports/compact_candidate.json'
    if not source.exists():raise ConfigError('run compact candidate study before structural screening')
    candidate=json.loads(source.read_text())
    if candidate['fingerprint']!=candidate_fingerprint(root):
        raise ConfigError('compact candidate report is stale; refusing structural load extraction')
    spec=load_yaml(root/'data/compact_structure.yaml');assumptions=spec['assumptions']
    objects,_,info=build(root);shapes={p.name:p.shape.val() for p in objects}
    cfg,parts=load_coupled(root);criteria=load_engineering(root)[0]
    motor=parts[cfg['reference']['motor']]['values']
    completed=[(bank,name,m) for bank,v in candidate['variants'].items() for name,m in v['cases'].items()
               if 'solver_failure' not in m]
    peak_bank,peak_case,peak_metrics=max(completed,key=lambda v:v[2]['worst_peak_tension_n'])
    observed_force=peak_metrics['worst_peak_tension_n']
    current=max(m[k] for _,_,m in completed for k in m if k.endswith('.max_current_a'))
    torque=max(motor['torque_peak_nm'],current*motor['kt_nm_per_a'])
    core=cfg['reference']['core_radius_mm'];rope=parts[cfg['reference']['rope']]['values']['diameter_mm']
    stall_force=motor['torque_peak_nm']*cfg['reference']['ratio']*cfg['reference']['efficiency']/((core+rope/2)/1000)
    force=max(observed_force,stall_force,lbf_to_n(criteria['force_peak_lbf']['value']))
    small_r=info['layout']['belt_pitch_mm']*info['layout']['pinion_teeth']/(2*math.pi)
    large_r=small_r*cfg['reference']['ratio']
    centres=math.dist(info['layout']['motor_axis_xy_mm'],info['layout']['drum_axis_xy_mm'])
    angle=math.asin((large_r-small_r)/centres)
    difference=torque/(small_r/1000)
    z=lambda name:shapes[name].Center().z
    bounds=lambda name:shapes[name].BoundingBox()
    motor_centres=[z('motor_bearing_0'),z('motor_bearing_1')]
    drum_centres=[z('drum_bearing_0'),z('drum_bearing_1')]
    belt_z=z('pinion');drum_fix_z=bounds('drum_top_bridge').zmin
    rope_range=[info['layout']['drum_bottom_mm']+info['layout']['drum_flange_thickness_mm']+rope/2,
                info['layout']['drum_bottom_mm']+info['layout']['drum_flange_thickness_mm']+
                cfg['reference']['turns_per_layer']*rope-rope/2]
    motor_d=bounds('motor_spindle').xlen;drum_d=bounds('drum_dead_shaft').xlen
    results=[]
    for pretension,rope_z in itertools.product(assumptions['belt_pretension_per_span_n'],rope_range):
        # If the nominal preload cannot keep the slack span taut, retain that
        # failure and use a nonnegative lower-bound tension resultant for reactions.
        taut=2*pretension>difference
        total=max(2*pretension,difference)
        wheel_force=np.array([-math.cos(angle)*total,math.sin(angle)*difference])
        motor_force=-wheel_force;rope_force=np.array([force,0.])
        ml,mu,mf,mm=bearing_reactions(motor_centres,[(belt_z,motor_force)])
        dl,du,df,dm=bearing_reactions(drum_centres,[(belt_z,wheel_force),(rope_z,rope_force)])
        motor_moment=float(np.linalg.norm(motor_force))*(belt_z-motor_centres[-1])
        # Shaft fixed at top: vector bending moment magnitude from all transverse loads.
        drum_moment=float(np.linalg.norm((belt_z-drum_fix_z)*wheel_force+(rope_z-drum_fix_z)*rope_force))
        motor_vm=shaft_stress(motor_moment,torque*1000,motor_d)
        drum_vm=shaft_stress(drum_moment,0,drum_d) # stationary shaft: rotor torque is not shaft torsion
        motor_load=max(float(np.linalg.norm(ml)),float(np.linalg.norm(mu)))
        drum_load=max(float(np.linalg.norm(dl)),float(np.linalg.norm(du)))
        motor_factor=spec['motor_bearing']['static_n']/motor_load
        drum_factor=info['layout']['drum_bearing']['static_n']/drum_load
        mb=bounds('motor_carrier_bridge');db=bounds('drum_top_bridge')
        motor_bridge_moment=float(np.linalg.norm(motor_force))*abs(belt_z-z('motor_carrier_bridge'))
        motor_bridge_stress=3*motor_bridge_moment/(mb.ylen*mb.zlen**2)
        drum_bridge_stress=3*drum_moment/(db.ylen*db.zlen**2)
        failed=[]
        if not taut:failed.append('nominal belt preload loses slack-side tension')
        for label,value,limit in (
                ('motor spindle equivalent stress',motor_vm,assumptions['steel_allowable_mpa']),
                ('drum shaft equivalent stress',drum_vm,assumptions['steel_allowable_mpa']),
                ('motor bridge beam surrogate',motor_bridge_stress,assumptions['aluminium_allowable_mpa']),
                ('drum bridge beam surrogate',drum_bridge_stress,assumptions['aluminium_allowable_mpa'])):
            if value>limit:failed.append(label)
        for label,value in (('motor bearing static factor',motor_factor),('drum bearing static factor',drum_factor)):
            if value<assumptions['bearing_static_factor_min']:failed.append(label)
        results.append(dict(pretension_per_span_n=pretension,rope_height_mm=rope_z,
            nominal_slack_side_positive=taut,belt_tension_difference_n=difference,belt_total_tension_n=total,
            motor_bearing_reactions_n=[ml.tolist(),mu.tolist()],drum_bearing_reactions_n=[dl.tolist(),du.tolist()],
            motor_bearing_peak_n=motor_load,drum_bearing_peak_n=drum_load,
            motor_bearing_static_factor=motor_factor,drum_bearing_static_factor=drum_factor,
            motor_spindle_stress_mpa=motor_vm,drum_shaft_stress_mpa=drum_vm,
            motor_bridge_surrogate_stress_mpa=motor_bridge_stress,drum_bridge_surrogate_stress_mpa=drum_bridge_stress,
            minimum_drum_bridge_surrogate_thickness_mm=math.sqrt(3*drum_moment/(db.ylen*assumptions['aluminium_allowable_mpa'])),
            max_force_residual_n=max(mf,df),max_moment_residual_nmm=max(mm,dm),failed_checks=failed))
    h=hashlib.sha256(source.read_bytes()+(root/'data/compact_structure.yaml').read_bytes()+Path(__file__).read_bytes())
    report={'fingerprint':h.hexdigest(),'candidate_fingerprint':candidate['fingerprint'],'assessment':'REVISE',
            'load_envelope':dict(observed_peak_n=observed_force,peak_bank=peak_bank,peak_case=peak_case,
                stall_force_screen_n=stall_force,selected_rope_force_n=force,selected_motor_torque_nm=torque,
                observed_max_current_a=current,belt_tension_difference_n=difference),
            'geometry':dict(motor_bearing_centres_mm=motor_centres,drum_bearing_centres_mm=drum_centres,
                belt_height_mm=belt_z,rope_height_range_mm=rope_range,motor_spindle_diameter_mm=motor_d,
                drum_shaft_diameter_mm=drum_d),
            'assumptions':assumptions,'motor_bearing_source':spec['motor_bearing'],'cases':results,
            'load_scope':'Uncorrelated maxima and winding-height corners; not a correlated transient structural solution',
            'qualified':False}
    (root/'reports/compact_structure.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    lines=['# Compact mechanical load-path screen','',f'Fingerprint: `{report["fingerprint"]}`','',
           '**Assessment: REVISE.** This uses current CAD bearing/support locations and the compact '
           'candidate force/current envelope. It does not qualify joints, fatigue, mounts or hardware.','',
           f'Rope-force corner: {force:.1f} N, the maximum of the owner target, documented peak-torque '
           f'stall screen ({stall_force:.1f} N) and simulated peak ({observed_force:.1f} N; '
           f'{peak_bank}/{peak_case}). Motor torque corner: {torque:.2f} Nm, the maximum of catalog '
           'peak torque and the simulated current × Kt. These maxima may occur at different times.','',
           f'Motor bearing centers: {motor_centres} mm; drum bearings: {drum_centres} mm; belt height '
           f'{belt_z:g} mm. Motor spindle diameter {motor_d:g} mm; drum shaft {drum_d:g} mm.','',
           f'[NSK 6000 source]({spec["motor_bearing"]["source"]}): dynamic 5050 N, static 1970 N, '
           'accessed 2026-11-02. Static rating is a comparison, not an allowable service load or fatigue life. '
           'NSK 6005 data and source are in `configs/compact_package.yaml`.','',
           '| Preload N/span | Rope z mm | Motor bearing N | Motor C0/P | Drum bearing N | Drum C0/P | Spindle MPa | Drum bridge surrogate MPa | Failed screens |',
           '|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for row in results:
        lines.append(f'| {row["pretension_per_span_n"]} | {row["rope_height_mm"]:.1f} | {row["motor_bearing_peak_n"]:.0f} | '
            f'{row["motor_bearing_static_factor"]:.2f} | {row["drum_bearing_peak_n"]:.0f} | {row["drum_bearing_static_factor"]:.2f} | '
            f'{row["motor_spindle_stress_mpa"]:.1f} | {row["drum_bridge_surrogate_stress_mpa"]:.1f} | {", ".join(row["failed_checks"]) or "none"} |')
    lines += ['','## Method and limits','',
        'Two-bearing reactions satisfy transverse force and moment equilibrium in two directions. '
        'The open belt uses exact tangent directions; tension difference is motor torque / pinion pitch '
        'radius. When the proposed preload gives a nonpositive slack side, the screen fails and a '
        'nonnegative lower-bound resultant is used for reaction estimates. This does not establish '
        'that the belt transmits the modeled torque or survives it. Tooth load, pretension setting, '
        'belt compliance and tensioner qualification remain open.','',
        'Shaft equivalent stress combines circular-section bending and torsion. The stationary drum '
        'dead shaft has no assumed rotor drive torsion. Shaft shoulders, fatigue, fits, keys and '
        'bearing axial loads are omitted. Generic stress allowables and the proposed C0/P ≥ 2 '
        'comparison are assumptions, not manufacturer approvals.','',
        assumptions['bridge_basis']+' The plate surrogate uses σ = 3M/(b t²). '
        'It is an analytical rejection indicator; full plate action can change the result. Structural '
        'qualification requires mesh/load convergence, actual bosses/joints, bolt preload and positive '
        'retention. A low shaft stress cannot qualify an unsupported bearing or thin bridge.','',
        'The compact body still has no engineered mounting bolt group, board attachment or adapter '
        'retention geometry. The legacy mount/board results are not reused for this candidate. '
        'Cable fatigue, guide contact, drum flanges/shell buckling and emergency arrestor loads remain '
        'unqualified. A collision-free model does not resolve any of these requirements.','',
        'Next revise the motor bearing span/overhang, spindle and bridge/shaft attachment design; '
        'choose a rated belt and pretension; then rerun layout, inertia, dynamics and structural checks.','',
        'Reproduce: `.venv/bin/python -m odrt.compact_structure` after the compact candidate study.','']
    (root/'reports/compact_structure.md').write_text('\n'.join(lines))
    return report


if __name__=='__main__':
    generate()
