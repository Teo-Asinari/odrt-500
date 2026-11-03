"""Compare a sourced roller-bearing revision against explicit load corners.

No CAD fit or rigid frame is proved by this calculation. The two-ended drum
shaft assumes supports whose required stiffness/joints still need engineering.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

from odrt.compact_structure import bearing_reactions,shaft_stress
from odrt.config import load_yaml


def screen(spec,existing,rope_force_n,motor_torque_nm):
    """Rows for every preload/rope-height/torque-sign corner at the given loads."""
    p=spec['revision_proposal']
    small=p['pinion_teeth']*p['pitch_mm']/(2*math.pi);large=p['wheel_teeth']*p['pitch_mm']/(2*math.pi)
    angle=math.asin((large-small)/115);difference=motor_torque_nm/(small/1000)
    force=np.array([0.,rope_force_n]) # side-exit rope; different from R1 +X routing
    rows=[]
    for preload,height,direction in itertools.product(p['pretension_per_span_n'],p['rope_height_range_mm'],(-1,1)):
        total=max(2*preload,difference)
        belt=np.array([-math.cos(angle)*total,direction*math.sin(angle)*difference])
        ml,mu,mf,mm=bearing_reactions(p['motor_bearing_centres_mm'],[(p['belt_centre_z_mm'],-belt)])
        dl,du,df,dm=bearing_reactions(p['drum_bearing_centres_mm'],[(p['belt_centre_z_mm'],belt),(height,force)])
        sl,su,sf,sm=bearing_reactions(p['shaft_support_z_mm'],[(p['belt_centre_z_mm'],belt),(height,force)])
        motor_load=max(np.linalg.norm(ml),np.linalg.norm(mu));drum_load=max(np.linalg.norm(dl),np.linalg.norm(du))
        motor_moment=np.linalg.norm(belt)*(p['belt_centre_z_mm']-p['motor_bearing_centres_mm'][-1])
        # Internal moment of the simply supported shaft: extrema occur at applied load stations.
        shaft_moment=0.
        for z in sorted([*p['shaft_support_z_mm'],height,p['belt_centre_z_mm']]):
            moment=(z-p['shaft_support_z_mm'][0])*sl
            for load_z,load in ((height,force),(p['belt_centre_z_mm'],belt)):
                if load_z<z:moment+=(z-load_z)*load
            shaft_moment=max(shaft_moment,float(np.linalg.norm(moment)))
        motor_vm=shaft_stress(motor_moment,motor_torque_nm*1000,15)
        drum_vm=shaft_stress(shaft_moment,0,25)
        motor_factor=spec['motor_bearing']['static_n']/motor_load
        drum_factor=min(spec['drum_floating']['static_n'],spec['drum_locating']['static_n'])/drum_load
        failed=[]
        if 2*preload<=difference:failed.append('nonpositive nominal slack tension')
        if motor_vm>existing['steel_allowable_mpa']:failed.append('motor shaft stress')
        if drum_vm>existing['steel_allowable_mpa']:failed.append('drum shaft stress')
        if motor_factor<existing['bearing_static_factor_min']:failed.append('motor bearing static factor')
        if drum_factor<existing['bearing_static_factor_min']:failed.append('drum bearing static factor')
        rows.append(dict(preload_n=preload,rope_z_mm=height,torque_direction=direction,
            motor_bearing_peak_n=float(motor_load),drum_bearing_peak_n=float(drum_load),
            motor_bearing_static_factor=float(motor_factor),drum_bearing_static_factor=float(drum_factor),
            motor_shaft_stress_mpa=float(motor_vm),drum_shaft_stress_mpa=float(drum_vm),
            base_reaction_n=sl.tolist(),deck_reaction_n=su.tolist(),
            max_force_residual_n=max(mf,df,sf),max_moment_residual_nmm=max(mm,dm,sm),failed_checks=failed))
    return rows,difference,2*(large+1)


def generate(root=Path('.')):
    root=Path(root);source=root/'data/revision_support.yaml';spec=load_yaml(source)
    p=spec['revision_proposal'];existing=load_yaml(root/'data/compact_structure.yaml')['assumptions']
    rows,difference,outer=screen(spec,existing,p['rope_force_comparison_n'],p['motor_torque_comparison_nm'])
    digest=hashlib.sha256(source.read_bytes()+(root/'data/compact_structure.yaml').read_bytes()+Path(__file__).read_bytes()).hexdigest()
    r={'fingerprint':digest,'assessment':'REVISE; support comparison only','sources':spec,
       'belt_tension_difference_n':difference,'wheel_outer_diameter_claim_mm':outer,
       'checks_passed':sum(not row['failed_checks'] for row in rows),'cases':rows,
       'limits':['Ideal radial supports; deck/base/sidewall stiffness and joints are not verified.',
        'Shaft shoulders, fit stress, axial load, cage/lubrication/minimum load, sealing and fatigue remain open.',
        '24/120 pulleys are proposed custom envelopes; no rated belt/teeth/hub design is established.',
        'The R2 CAD and simulated R2 loads are in r2_package.md and r2_candidate.md; controller calibration is unchanged.']}
    (root/'reports/support_revision.json').write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    lines=['# Roller-bearing and two-ended-shaft revision screen','',f'Fingerprint: `{digest}`','',
        '**REVISE: comparison only, not a selected complete design.** '
        'The proposed 24/120-tooth stage is 5:1. Motor supports use opposed NJ 202 ECP roller bearings; '
        'the drum uses NU205EM floating and NUP205EM locating types on a 25 mm shaft supported at both ends. '
        'The side-exit rope force is +Y, and both torque directions are checked.','',
        f'Load corners: {p["rope_force_comparison_n"]} N rope force and {p["motor_torque_comparison_nm"]} Nm motor torque. '
        f'Belt tension difference: {difference:.1f} N. Outer wheel envelope: {outer:.2f} mm. '
        'These exceed R1 observed maxima; [r2_candidate.md](r2_candidate.md) repeats the screen at the simulated R2 loads.','',
        '| Preload N/span | Rope z mm | Torque sign | Motor C0/P | Drum C0/P | Motor shaft MPa | Drum shaft MPa | Failed screens |',
        '|---:|---:|---:|---:|---:|---:|---:|---|']
    for x in rows:lines.append(f'| {x["preload_n"]} | {x["rope_z_mm"]} | {x["torque_direction"]} | '
        f'{x["motor_bearing_static_factor"]:.2f} | {x["drum_bearing_static_factor"]:.2f} | '
        f'{x["motor_shaft_stress_mpa"]:.1f} | {x["drum_shaft_stress_mpa"]:.1f} | {", ".join(x["failed_checks"]) or "none in these comparisons"} |')
    lines+=['','## Primary sources','']+[f'- [{spec[key]["part"]}]({spec[key]["source"]}), accessed {spec[key]["accessed"]}.'
                                              for key in ('motor_bearing','drum_floating','drum_locating','cell')]
    lines+=['','The 20-cell TV-series proposal has 3 V-rated cells with 11 mΩ initial maximum ESR, in the '
        'same 18.5 × 60.5 mm maximum body claim. At 52 V, matched cell voltage is 2.6 V and pack rating '
        'is 60 V. Individual-cell balance/protection and thermal capacity still need engineering; the '
        '20 J/K thermal capacity is explicitly assumed, not a vendor specification.','',
        '## Remaining work','']+['- '+v for v in r['limits']]
    lines+=['','Frame reactions are recorded in JSON. They must be applied to the actual deck/sidewalls/base '
        'and fasteners; the old slender posts cannot simply be assumed rigid. No frame or mount qualification '
        'is established by improved bearing/shaft numbers.','',
        'Reproduce: `.venv/bin/python -m odrt.support_revision`.','']
    (root/'reports/support_revision.md').write_text('\n'.join(lines));return r


if __name__=='__main__':
    generate()
