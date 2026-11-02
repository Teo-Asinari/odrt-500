"""ADR-002 integration study: per-unit space claim, mount reactions and common board.

All dimensions/properties without a component source are A-026 proposals. Capacity
requirements do not qualify a wall, rack, door, bracket or board attachment.
"""
from __future__ import annotations

import math
from pathlib import Path

from odrt.config import ConfigError, check_keys, load_yaml, number
from odrt.units import lbf_to_n


def load_modular(path):
    d = load_yaml(path)
    check_keys(d, str(path), ['units', 'compact_target_l', 'shell_mm', 'clearance_mm', 'tray_gap_mm',
                              'fleet_angle_deg', 'interface', 'board'])
    for key in ('compact_target_l', 'shell_mm', 'clearance_mm', 'tray_gap_mm', 'fleet_angle_deg'):
        d[key] = number(d[key], f'{path}.{key}', minimum=0, exclusive_minimum=True)
    if d['units'] != 2 or isinstance(d['units'], bool):
        raise ConfigError(f'{path}.units: ADR-002 requires two units')
    if d['fleet_angle_deg'] > 15:
        raise ConfigError(f'{path}.fleet_angle_deg: must be <= 15')
    it = d['interface']
    check_keys(it, f'{path}.interface', ['bolt_spacing_mm', 'bolt_area_mm2', 'allowable_mpa', 'plate_thickness_mm'])
    if not isinstance(it['bolt_spacing_mm'], list) or len(it['bolt_spacing_mm']) != 2:
        raise ConfigError(f'{path}.interface.bolt_spacing_mm: need two spacings')
    it['bolt_spacing_mm'] = [number(v, 'bolt spacing', minimum=0, exclusive_minimum=True)
                              for v in it['bolt_spacing_mm']]
    for key in ('bolt_area_mm2', 'allowable_mpa', 'plate_thickness_mm'):
        it[key] = number(it[key], f'{path}.interface.{key}', minimum=0, exclusive_minimum=True)
    board = d['board']
    check_keys(board, f'{path}.board', ['width_mm', 'depth_mm', 'thickness_mm', 'foot_half_spacing_mm',
                                      'youngs_gpa', 'allowable_mpa', 'density_kg_m3', 'deflection_limit_mm'])
    for key in board:
        board[key] = number(board[key], f'{path}.board.{key}', minimum=0, exclusive_minimum=True)
    if board['foot_half_spacing_mm'] >= board['width_mm'] / 2:
        raise ConfigError(f'{path}.board: feet must lie between unit attachment lines')
    return d


def mount_cases(force_n, lever_mm, interface):
    """Six unit-axis pulls, four bolts in the XZ plane; Y is mount normal.

    No friction credit. Linear bolt group, moment about Y gives in-plane torsion;
    moments about X/Z give bolt tension. Report worst positive tension per bolt.
    """
    sx, sz = (v / 1000 for v in interface['bolt_spacing_mm'])
    r = [v / 1000 for v in lever_mm]
    out = []
    for axis, name in enumerate(('lateral', 'normal', 'vertical')):
        for sign in (-1, 1):
            f = [0., 0., 0.]
            f[axis] = sign * force_n
            mx = r[1] * f[2] - r[2] * f[1]
            my = r[2] * f[0] - r[0] * f[2]
            mz = r[0] * f[1] - r[1] * f[0]
            j = sx**2 + sz**2
            max_t, max_s, max_vm = 0., 0., 0.
            for x in (-sx / 2, sx / 2):
                for z in (-sz / 2, sz / 2):
                    tension = max(0., f[1] / 4 + mz * x / sx**2 - mx * z / sz**2)
                    shear = math.hypot(f[0] / 4 + my * z / j, f[2] / 4 - my * x / j)
                    vm = math.sqrt(tension**2 + 3 * shear**2) / interface['bolt_area_mm2']
                    max_t, max_s, max_vm = max(max_t, tension), max(max_s, shear), max(max_vm, vm)
            out.append(dict(case=f'{name} {sign:+d}', force_n=force_n, moment_nm=math.sqrt(mx*mx+my*my+mz*mz),
                            bolt_tension_n=max_t, bolt_shear_n=max_s, stress_mpa=max_vm,
                            bolt_ok=max_vm <= interface['allowable_mpa']))
    return out


def board_check(board, per_unit_force_n):
    """Symmetric four-point bending: outer units pull up, inner feet push down.

    Constant moment between feet. Deflection at each outer attachment relative
    to the foot includes rotation of the centre span plus overhang bending.
    Joint compliance, local pull-through and asymmetric pulls are not covered.
    """
    w, depth, t, foot = (board[k] / 1000 for k in
                         ('width_mm', 'depth_mm', 'thickness_mm', 'foot_half_spacing_mm'))
    a, b = w / 2 - foot, 2 * foot
    inertia = depth * t**3 / 12
    moment = per_unit_force_n * a
    stress = moment * t / 2 / inertia / 1e6
    defl = per_unit_force_n * (a**3 / 3 + a**2 * b / 2) / (board['youngs_gpa'] * 1e9 * inertia) * 1000
    return dict(moment_nm=moment, stress_mpa=stress, deflection_mm=defl,
                stress_ok=stress <= board['allowable_mpa'], deflection_ok=defl <= board['deflection_limit_mm'],
                mass_kg=w * depth * t * board['density_kg_m3'])


def placement(cfg, mech_bounds, drum_width_mm, axis_exit_mm, el_parts):
    """Stack electrical trays above the retained mechanism; explicit rope corridor.

    Bounding boxes include each component's estimated service gap, but do not
    demonstrate cable routing, isolation, ventilation or assembly access.
    """
    c, s = cfg['clearance_mm'], cfg['shell_mm']
    xmin, ymin, zmin, xmax, ymax, zmax = mech_bounds
    shift = (s+c-xmin, s+c-ymin, s+c-zmin)
    mech_dims = (xmax-xmin, ymax-ymin, zmax-zmin)
    drum_x, drum_y, exit_z = (axis_exit_mm[i]+shift[i] for i in range(3))
    fleet = drum_width_mm / 2 / math.tan(math.radians(cfg['fleet_angle_deg']))
    radius = 30.  # retained 4 mm rope / 60 mm pitch-diameter sheave, fatigue review open
    yc = max(drum_y+fleet, ymax+shift[1]+c+radius)
    # Electronics arranged in three rows; each row is clear of every neighbour.
    rows = [('psu', 'brake_resistor'), ('cap_bank',), ('drive', 'drive_heatsink', 'safety_mcu', 'sto_relay', 'load_cell'),
            ('fan', 'mains_inlet', 'estop')]
    dims = {k: p.dims_mm for k,p in el_parts.items()}
    cell = dims['cap_cell_large']
    dims['cap_bank'] = (8*(cell[0]+1), 3*(cell[1]+1), cell[2]+8)
    ztray = zmax+shift[2]+cfg['tray_gap_mm']
    boxes = []
    row_y = s+c
    for row in rows:
        x = s+c
        for key in row:
            dim = dims[key]
            boxes.append(dict(name=key, corner=(x, row_y, ztray), dims=dim))
            x += dim[0]+c
        row_y += max(dims[key][1] for key in row)+c
    width = max(xmax+shift[0], max(b['corner'][0]+b['dims'][0] for b in boxes), drum_x+95)+c+s
    depth = max(yc+radius+95, row_y)+c+s
    height = max(ztray+max(b['dims'][2] for b in boxes), exit_z+2*radius+10)+c+s
    # Straight drum-to-sheave path below electronics; 90 mm fleet corridor, 30 mm high.
    corridor = dict(name='rope corridor', corner=(drum_x-45, drum_y, exit_z-15), dims=(90, yc-drum_y, 30))
    exit_point = (drum_x, yc+radius, height)
    # Side-mounted interface plane: rear face, plate centred in X and Z.
    lever = (exit_point[0]-width/2, exit_point[1], exit_point[2]-height/2)
    volume = width*depth*height/1e6
    clashes = box_clashes(boxes+[dict(name='mechanism',corner=(s+c,s+c,s+c),dims=mech_dims)])
    clashes += box_clashes(boxes+[corridor])
    vertical = dict(name='vertical rope corridor', corner=(exit_point[0]-45,exit_point[1]-45,exit_z+radius),
                    dims=(90,90,height-exit_z-radius))
    clashes += box_clashes(boxes+[vertical])
    return dict(dimensions_mm=(width,depth,height), shift_mm=shift, electronics=boxes, rope=corridor,
                exit_mm=exit_point, vertical_rope=vertical, sheave_center_mm=(drum_x,yc,exit_z+radius), lever_mm=lever,
                volume_l=volume, compact_ok=volume <= cfg['compact_target_l'], clashes=clashes,
                fleet_distance_mm=fleet, electronics_z_mm=ztray)


def box_clashes(boxes):
    out=[]
    for i,a in enumerate(boxes):
        for b in boxes[i+1:]:
            overlap=[min(a['corner'][j]+a['dims'][j],b['corner'][j]+b['dims'][j])-
                     max(a['corner'][j],b['corner'][j]) for j in range(3)]
            if min(overlap)>1e-6:
                out.append((a['name'],b['name'],math.prod(overlap)))
    return out


def exploded_parts(parts, depth_mm):
    """Presentation offsets in mm; these do not specify an assembly sequence."""
    from odrt.cad import Part

    result = []
    for part in parts:
        name = part.name
        offset = (0, 0, 0)
        if part.material == 'black':
            offset = (0, depth_mm + 180, 220)
        elif part.material == 'electronics':
            offset = (0, 0, 200)
        elif name == 'universal mount space claim':
            offset = (0, -180, 0)
        elif name == 'exit turning sheave':
            offset = (0, 0, 120)
        elif name == 'shaft':
            offset = (300, 0, 70)
        elif name.startswith(('drum', 'cable layers')):
            offset = (0, 0, 70)
        elif name.startswith(('side plate', 'bearing', 'belt wheel', 'motor', 'pinion')):
            side = -1 if 'left' in name else 1
            distance = 100 if name.startswith(('side plate', 'bearing')) else 210
            if name.startswith('motor'):
                distance = 310
            offset = (side * distance, -60 if name.startswith(('motor', 'pinion')) else 0, 70)
        result.append(Part(name, part.shape.translate(offset), part.material, part.moving))
    return result


def build_and_report(inputs, sizes, out, reports):
    """Generate the current modular concept; legacy platform remains in source only."""
    from odrt import cad, electronics, swivel
    from odrt.reporting import write_swivel_report
    import dataclasses
    from odrt.drivetrain import Drum
    cfg=load_modular(inputs.root/'configs/modular.yaml')
    el=electronics.load_electronics(inputs.root/'data/electronics.csv')
    st=inputs.structure
    opt=inputs.options[st.design]
    mech,geo=cad.build(st,opt,inputs.common,sizes)
    bounds=[p.shape.val().BoundingBox() for p in mech]
    bb=(min(b.xmin for b in bounds),min(b.ymin for b in bounds),min(b.zmin for b in bounds),
        max(b.xmax for b in bounds),max(b.ymax for b in bounds),max(b.zmax for b in bounds))
    lay=placement(cfg,bb,Drum(opt.architecture,inputs.common).width_m*1000,(0,0,geo['cable_exit_height_mm']),el)
    design_peak=max(sizes['stall_tension_lbf'],sizes['observed_fault_peak_lbf'])
    mounts=mount_cases(lbf_to_n(design_peak),lay['lever_mm'],cfg['interface'])
    board=board_check(cfg['board'],lbf_to_n(design_peak))
    cq=cad._cq()
    parts=[cad.Part(p.name,p.shape.translate(lay['shift_mm']),p.material,p.moving) for p in mech]
    for b in lay['electronics']:
        shape=cq.Workplane('XY').box(*b['dims'],centered=False).translate(b['corner'])
        parts.append(cad.Part(b['name'],shape,'electronics',False))
    w,d,h=lay['dimensions_mm']; shell=cfg['shell_mm']
    outer=cq.Workplane('XY').box(w,d,h,centered=False)
    inner=cq.Workplane('XY').box(w-2*shell,d-2*shell,h-2*shell,centered=False).translate((shell,shell,shell))
    skin=outer.cut(inner)
    # Aperture is a space claim, no claim that the rope guard / swivel is complete.
    ex,ey,_=lay['exit_mm']
    skin=skin.cut(cq.Workplane('XY').circle(45).extrude(2*shell).translate((ex,ey,h-shell)))
    parts.append(cad.Part('black metallic enclosure',skin,'black',False))
    cx,cy,cz=lay['sheave_center_mm']
    sheave=cq.Workplane('YZ').circle(30).circle(8).extrude(16).translate((cx-8,cy,cz))
    parts.append(cad.Part('exit turning sheave',sheave,'plate',True))
    # Rope route: horizontal fleet corridor then a vertical exit, reserved rather than a fake taut path.
    rope=lay['rope']
    keep=cq.Workplane('XY').box(*rope['dims'],centered=False).translate(rope['corner'])
    vr=lay['vertical_rope']
    vkeep=cq.Workplane('XY').box(*vr['dims'],centered=False).translate(vr['corner'])
    keep=keep.union(vkeep)
    # Show keep-out only in cutaway, it is not a physical part or a mass contribution.
    it=cfg['interface']; sw,sh=it['bolt_spacing_mm']; t=it['plate_thickness_mm']
    if sw+40>w or sh+40>h:
        raise ConfigError('modular interface bolt spacing does not fit the unit rear face')
    plate=cq.Workplane('XZ').box(sw+40,sh+40,t).translate((w/2,-t/2,h/2))
    for x in (-sw/2,sw/2):
        for z in (-sh/2,sh/2):
            hole=cq.Workplane('XZ').circle(6).extrude(2*t,both=True).translate((w/2+x,0,h/2+z))
            plate=plate.cut(hole)
    parts.append(cad.Part('universal mount space claim',plate,'plate',False))
    masses=cad.mass_kg(parts,st,opt.component.mass_kg or 0.)
    # Black skin is aluminium in this concept; material key controls its display color.
    known_mass=sum(masses.values())+skin.val().Volume()*1e-9*st.plate.density_kg_m3
    # Full STEP plus full/cutaway/exploded GLBs.
    out=Path(out); reports=Path(reports)
    out.mkdir(parents=True,exist_ok=True); (reports/'figures').mkdir(parents=True,exist_ok=True)
    assy=cad.assemble(parts); step=out/'odrt250_unit.step'; assy.save(str(step))
    for tag in ('full','cutaway','exploded'):
        selected=[]
        for p in exploded_parts(parts, d) if tag == 'exploded' else parts:
            if tag=='cutaway' and p.material=='black': continue
            shape=p.shape
            selected.append(cad.Part(p.name,shape,p.material,p.moving))
        if tag=='cutaway': selected.append(cad.Part('rope routing keep-out',keep,'none',False))
        path=out/f'odrt250_unit_{tag}.glb'
        cad.assemble(selected).save(str(path),exportType='GLTF'); cad.gltf_to_metres_y_up(path)
    boardparts=[]
    bc=cfg['board']; bw,bd,bt=(bc[k] for k in ('width_mm','depth_mm','thickness_mm'))
    boardshape=cq.Workplane('XY').box(bw,bd,bt,centered=False).translate((w+20,0,0))
    boardparts.append(cad.Part('common board',boardshape,'board',False))
    # Units flank the board; both exit cables rise vertically. Right unit is mirrored.
    for side in (0,1):
        for p in parts:
            shape=p.shape if side==0 else p.shape.mirror('YZ').translate((2*w+bw+40,0,0))
            boardparts.append(cad.Part(f'unit {side+1} {p.name}',shape,p.material,p.moving))
    # Gaps deliberately reserved for adapters. No pretend fasteners connect the parts.
    for tag,export in (('step','STEP'),('glb','GLTF')):
        path=out/f'odrt500_modular_board.{tag}'
        cad.assemble(boardparts).save(str(path),exportType=export)
        if tag=='glb': cad.gltf_to_metres_y_up(path)
    exploded_board = [cad.Part('common board', boardshape.translate((0, 0, -120)), 'board', False)]
    for side in (0, 1):
        for p in exploded_parts(parts, d):
            shape = (p.shape.translate((-350, 0, 0)) if side == 0 else
                     p.shape.mirror('YZ').translate((2*w+bw+390, 0, 0)))
            exploded_board.append(cad.Part(f'unit {side+1} {p.name}', shape, p.material, p.moving))
    exploded_path = out / 'odrt500_modular_board_exploded.glb'
    cad.assemble(exploded_board).save(str(exploded_path), exportType='GLTF')
    cad.gltf_to_metres_y_up(exploded_path)
    for name,ps in (('cad_iso',parts),('cad_plan',parts),('cad_platform_iso',boardparts)):
        direction=(0,0,-1) if name=='cad_plan' else (1,1.2,-.8)
        cq.exporters.export(cq.Workplane().add(cad.assemble(ps).toCompound().mirror('XY')),
                            str(reports/'figures'/f'{name}.svg'),exportType='SVG',
                            opt={'projectionDir':direction,'showAxes':False,'width':640,'height':420,
                                 'showHidden':False,'strokeWidth':.4})
    budget=electronics.budget(inputs,load_yaml(inputs.root/'configs/electronics.yaml'))
    report(inputs,cfg,lay,mounts,board,known_mass,design_peak,budget,reports)
    # The local exit mechanics still use the swivel load model; use at least the observed snap ratio.
    swcfg=swivel.load_swivel(inputs.root/'configs/swivel.yaml')
    swcfg=dataclasses.replace(swcfg,snap_factor=max(swcfg.snap_factor,design_peak/inputs.envelope.peak_tension_lbf))
    write_swivel_report(inputs,swcfg,swivel.envelope(swcfg),reports)
    clashes=cad.interferences(mech)+lay['clashes']
    print(f'Modular unit {w:.0f} x {d:.0f} x {h:.0f} mm, {lay["volume_l"]:.1f} L; '
          f'{len(clashes)} mechanism / placement interferences; compact target met: {lay["compact_ok"]}')
    return 1 if clashes else 0


def report(inputs,cfg,lay,mounts,board,mass,design_peak,b,reports):
    from odrt.reporting import _header
    w,d,h=lay['dimensions_mm']
    lines=_header('Iteration 3 modular units and mounting',inputs)
    lines += ['ADR-002: two independent 250 lbf cable units, each with mains input, motor, drive and buffer. '
              '500 lbf combined assumes equal loading on one bar; coupled bar dynamics and asymmetric faults are not simulated (A-026).','',
              f'One-unit space claim: **{w:.0f} × {d:.0f} × {h:.0f} mm**, {lay["volume_l"]:.1f} L. '
              f'The provisional {cfg["compact_target_l"]:g} L target is **{"met" if lay["compact_ok"] else "NOT met"}**. '
              f'Known modeled metal and motor mass: **≥ {mass:.1f} kg per unit**; electronics, rope and hardware masses are missing.','',
              'The retained drum, belt and 4° fleet angle dominate the package. This is an integration reference, '
              'not a compact Voltra-sized result. A narrower/multilayer drum or a qualified cable guide is the next packaging trade study.','',
              f'Drum-to-sheave minimum fleet distance: {lay["fleet_distance_mm"]:.0f} mm. '
              f'Electronics sit on a separate tray at z = {lay["electronics_z_mm"]:.0f} mm. '
              f'Placement-box overlaps: {len(lay["clashes"])}. Electronic boxes are space claims, '
              'not detailed boards, wiring or safety clearances. Exit guard, tray supports and sheave axle/cheeks are not designed.','',
              '## Universal interface load cases','',
              f'Load magnitude: max(stall, safety-on simulated peak) = **{design_peak:.0f} lbf** per unit. '
              'Six principal directions screen component loads only; arbitrary combined pull directions need a continuous envelope. '
              'The same four-bolt XZ interface is proposed for all adapters. No friction credit; linear elastic bolt group.','',
              '| Pull direction | Force N | Moment N·m | Max bolt tension N | Max bolt shear N | Bolt equivalent MPa | Bolt stress check |',
              '|---|---:|---:|---:|---:|---:|---|']
    for r in mounts:
        lines.append(f'| {r["case"]} | {r["force_n"]:.0f} | {r["moment_nm"]:.0f} | {r["bolt_tension_n"]:.0f} | '
                     f'{r["bolt_shear_n"]:.0f} | {r["stress_mpa"]:.1f} | {"pass" if r["bolt_ok"] else "FAIL"} |')
    required_area=max(r['stress_mpa'] for r in mounts)*cfg['interface']['bolt_area_mm2']/cfg['interface']['allowable_mpa']
    lines += ['', f'For this geometry and the worst screened direction, the bolt stress model requires at least '
              f'**{required_area:.0f} mm² tensile area per bolt**, versus the proposed '
              f'{cfg["interface"]["bolt_area_mm2"]:g} mm². Reducing the exit-to-mount lever or enlarging the bolt group '
              'is an alternative; neither qualifies the plate or substrate.', '', '| Adapter | Required load path / unresolved validation |','|---|---|',
              '| Board | Two unit retention joints and board edge adapters; symmetric bending below; local pull-through, one-sided pulls and torsion unresolved |',
              '| Wall | Interface forces and moments into a qualified bracket, anchors and specified substrate; no wall capacity established |',
              '| Rack | Clamp slip, rack tipping and tube crushing under interface forces/moments; no rack capacity established |',
              '| Door | Frame/door/hinge/closure load paths unknown; high-force operation remains unsupported |','',
              'Mount plate in CAD is a drilled space claim. Bolt stress alone does not establish plate strength, '
              'prying, fatigue, captive retention or adapter/substrate capacity. Rear-face interface permits different adapter orientations.','',
              '## Common board','',
              f'{cfg["board"]["width_mm"]:g} × {cfg["board"]["depth_mm"]:g} × {cfg["board"]["thickness_mm"]:g} mm; '
              f'estimated mass {board["mass_kg"]:.1f} kg. Generic plywood-like E and allowable stress are placeholders. '
              'Units pull up at the two edges and feet push down at the inner support lines. Both units conservatively reach the fault peak simultaneously.','',
              f'- Bending stress: {board["stress_mpa"]:.1f} MPa against {cfg["board"]["allowable_mpa"]:g} MPa: '
              f'**{"pass" if board["stress_ok"] else "FAIL"}**.',
              f'- Edge deflection relative to feet: {board["deflection_mm"]:.1f} mm against '
              f'{cfg["board"]["deflection_limit_mm"]:g} mm: **{"pass" if board["deflection_ok"] else "FAIL"}**.','',
              f'The same ideal beam model requires thickness ≥ '
              f'{cfg["board"]["thickness_mm"] * max((board["stress_mpa"]/cfg["board"]["allowable_mpa"])**.5, (board["deflection_mm"]/cfg["board"]["deflection_limit_mm"])**(1/3)):.1f} mm '
              'to meet both proposed criteria, before local joint or asymmetric-load checks.', '',
              'The rendered units flank the board with adapter gaps. Adapter geometry/fasteners are not supplied. '
              'The board assembly is not a qualified connected load path. Floor contact, unequal foot positions, '
              'one-unit pull, local bending and retention must be assessed before selecting a board.','',
              '## Standalone safety and two-unit operation','',
              '- Each unit needs local tension/speed sensing, watchdog, stop input, torque disable and power-loss braking. '
              'These cannot depend on a peer unit or board occupancy.',
              '- Board mode additionally needs authenticated adapter retention and board presence. Current deck-empty '
              'fault simulations are an ideal board-presence abstraction only.',
              '- Wall/rack mode must require a qualified adapter and installation; absence of a board must not be treated '
              'as permission to bypass retention checks. Mode detection and its fault behavior are not implemented.',
              '- Shared-bar operation needs independent stops plus a defined coordinated response when one unit loses '
              'power, sensing or communication. No validated two-unit safety protocol exists.',
              '- Snap-load arrestor, rope selection/fatigue, enclosure pinch guards, EMC and mains isolation remain open.','',
              'Exports: `build/cad/odrt250_unit.step`, `odrt250_unit_full.glb`, `_cutaway.glb`, `_exploded.glb`, '
              '`odrt500_modular_board.step` and `.glb`. Black enclosure styling is visual only.','']
    (reports/'modular.md').write_text('\n'.join(lines))
    for name,title,body in [
        ('cad.md','Current modular CAD',f'![Unit](figures/cad_iso.svg)\n\n![Plan](figures/cad_plan.svg)\n\n'
         f'Current unit and paired-board exports are listed in [modular.md](modular.md). Unit volume {lay["volume_l"]:.1f} L; '
         f'known modeled mass ≥ {mass:.1f} kg. Placement overlaps: {len(lay["clashes"])}. '
         'The detailed mechanism is retained; electronics and interface are bounding space claims. '
         'The previous floor-platform CAD is superseded and no longer generated.'),
        ('platform.md','Common board (ADR-002)', '![Paired units](figures/cad_platform_iso.svg)\n\n'
         'See [modular.md](modular.md) for board bending, adapter gaps, mount reactions and unresolved load paths. '
         'The earlier integrated floor platform is superseded.'),
        ('electronics.md','Per-unit electronics and power',
         f'Each unit: **{inputs.dynamics.supply_max_w:g} W** unsourced 48 V supply candidate, ideal '
         f'{inputs.dynamics.bus_c:g} F buffer and one ODrive S1. Supply efficiency 90% is assumed. '
         '22 large low-ESR cells are reserved in the package, with at least the modeled capacitance. '\
         'Balancing/pre-charge/fusing/discharge hardware is not dimensioned.\n\n'
         f'| Quantity | Per unit |\n|---|---:|\n| Motor peak / RMS A | {b["motor_peak_current_a"]:.1f} / {b["motor_window_rms_current_a"]:.1f} |\n'
         f'| Bus peak A | {b["bus_peak_current_a"]:.1f} |\n| Buffer estimated RMS A | {b["buffer_rms_current_a"]:.1f} |\n'
         f'| Large-cell ESR loss W / sag V | {b["buffer_loss_large_w"]:.1f} / {b["buffer_drop_large_v"]:.1f} |\n'
         f'| Small-cell ESR loss W / sag V | {b["buffer_loss_small_w"]:.1f} / {b["buffer_drop_small_v"]:.1f} |\n'
         f'| Heavy-set / session heat W | {b["set_heat_w"]:.0f} / {b["session_heat_w"]:.0f} |\n'
         f'| Estimated session air, passive / fan °C | {b["air_natural_c"]:.0f} / {b["air_fan_c"]:.0f} |\n\n'
         'Buffer current is estimated from analytical power swing; ESR heat/sag is not fed back into the dynamic model. '
         'The selected cells, wiring, thermal paths and supply derating are unresolved. The air estimate uses '
         'a conservative exposed skin-area assumption and does not establish winding temperature in the enclosure.\n\n'
         'Local power path: mains → supply → DC bus ↔ buffer/dump → drive → motor. '
         'Local safety controller monitors independent speed/tension, stop and mount state, and trips torque disable '
         'plus resistive phase braking. Board presence is an additional board-mode condition. '
         'The shared-bar coordination and mount-state electronics are not designed. '
         'See [modular.md](modular.md) for placements and remaining integration gaps.')]:
        (reports/name).write_text('\n'.join(_header(title,inputs))+body+'\n')
