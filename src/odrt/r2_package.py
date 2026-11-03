"""R2 compact integration: the support/power revision as one connected CAD.

Run python -m odrt.r2_package. Like R1, this is a space claim with explicit
collision and keepout checks; it does not establish strength, isolation,
cooling, rope life or feasibility. Heights shared with the support screen are
read from data/revision_support.yaml so the two cannot drift apart.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path

from odrt.cad import Part, _cq, assemble, gltf_to_metres_y_up
from odrt.compact_package import inertia_properties, overlaps
from odrt.config import ConfigError, load_yaml
from odrt.coupled import load_coupled

SOURCES = ('configs/r2_package.yaml', 'data/revision_support.yaml', 'data/revision_components.yaml',
           'configs/coupled.yaml', 'data/engineering_components.yaml')
ROTATING = ('drum', 'driven_wheel', 'motor_rotor_adapter', 'motor_spindle', 'pinion')


def package_fingerprint(root=Path('.')):
    root = Path(root); h = hashlib.sha256()
    for rel in SOURCES:
        h.update(rel.encode() + b'\0' + (root/rel).read_bytes() + b'\0')
    for module in ('r2_package.py', 'compact_package.py', 'cad.py'):
        h.update(module.encode() + b'\0' + Path(__file__).with_name(module).read_bytes() + b'\0')
    return h.hexdigest()


def build(root=Path('.')):
    root = Path(root); cq = _cq()
    layout = load_yaml(root/'configs/r2_package.yaml')
    support = load_yaml(root/'data/revision_support.yaml'); p = support['revision_proposal']
    supply = load_yaml(root/'data/revision_components.yaml')['epp500_54']['facts']
    cfg, parts = load_coupled(root)
    ref = dict(cfg['reference'], ratio=p['wheel_teeth']/p['pinion_teeth'])
    motor = parts[ref['motor']]['values']; rope_d = parts[ref['rope']]['values']['diameter_mm']
    mx, my = layout['motor_axis_xy_mm']; dx, dy = layout['drum_axis_xy_mm']
    centre = math.hypot(dx-mx, dy-my)
    small_r = p['pinion_teeth']*p['pitch_mm']/(2*math.pi); large_r = p['wheel_teeth']*p['pitch_mm']/(2*math.pi)
    face = p['pulley_face_mm']; gear_z = p['belt_centre_z_mm'] - face/2
    width = ref['turns_per_layer']*rope_d; core = ref['core_radius_mm']
    wind_lo = p['rope_height_range_mm'][0] - rope_d/2; wind_hi = p['rope_height_range_mm'][1] + rope_d/2
    if abs((wind_hi-wind_lo) - width) > 1e-6:
        raise ConfigError('rope height range does not match drum winding width')
    mb_w, db_w = support['motor_bearing']['dimensions_mm'][2], support['drum_floating']['dimensions_mm'][2]
    mb_bore, mb_od = (d/2 for d in support['motor_bearing']['dimensions_mm'][:2])
    db_bore, db_od = (d/2 for d in support['drum_floating']['dimensions_mm'][:2])
    if db_od >= core:
        raise ConfigError('drum bearings must fit inside the winding core')
    flange_t = layout['drum_flange_thickness_mm']; flange_r = layout['drum_flange_radius_mm']
    deck_lo, deck_hi = p['frame_deck_z_mm']; base_t = 2
    objects = []; fidelity = {}

    def add(name, shape, material, detail, moving=False):
        objects.append(Part(name, shape, material, moving)); fidelity[name] = detail

    def box(size, corner):
        return cq.Workplane('XY').box(*size, centered=False).translate(corner)

    def ring(x, y, z0, z1, outer, inner=0):
        wp = cq.Workplane('XY').workplane(offset=z0).center(x, y).circle(outer)
        if inner: wp = wp.circle(inner)
        return wp.extrude(z1-z0)

    def cylinder(radius, length, start, axis):
        direction = cq.Vector(*(1 if a == axis else 0 for a in 'xyz'))
        return cq.Workplane('XY').newObject([cq.Solid.makeCylinder(radius, length, cq.Vector(*start), direction)])

    ex, ey, ez = layout['envelope_mm']; wall = layout['wall_mm']
    add('base', box((ex, ey, base_t), (0, 0, 0)), 'plate', 'Proposed structural base; mounting joints unqualified')
    skin = box((ex, ey, ez-base_t), (0, 0, base_t)).cut(box((ex-2*wall, ey-2*wall, ez-2*wall), (wall, wall, base_t)))
    sx0, sx1 = layout['rope_exit']['slot_x_mm']
    skin = skin.cut(box((sx1-sx0, wall+1, wind_hi-wind_lo+4), (sx0, ey-wall-.5, wind_lo-2)))
    for claim in layout['electrical_space_claims']:
        if claim['name'] in ('mains_entry_and_filter', 'fan_and_duct_claim'):
            _, cy, cz = claim['corner_mm']; _, sy, sz = claim['size_mm']
            skin = skin.cut(box((wall+1, sy, sz), (ex-wall-.5, cy, cz)))
    add('enclosure_skin', skin, 'plate', '2 mm skin; +Y rope slot and +X inlet/fan openings; sealing and attachment unresolved')

    # Motor side: pedestal, envelope, rotating adapter/spindle/pinion, opposed roller bearings in a bridge housing.
    m0, m1 = layout['motor_z_mm']; a0, a1 = layout['rotor_adapter_z_mm']; motor_r = motor['diameter_mm']/2
    add('motor_pedestal', ring(mx, my, base_t, m0, motor_r), 'plate', 'Carrier interface; stator attachment unresolved')
    add('motor_envelope', ring(mx, my, m0, m1, motor_r), 'motor', 'Sourced RO100 outer envelope only')
    add('motor_rotor_adapter', ring(mx, my, a0, a1, 50), 'plate', 'Proposed rotating carrier; motor mating geometry unresolved', True)
    add('motor_spindle', ring(mx, my, a1, gear_z+face, mb_bore), 'shaft',
        f'Proposed {2*mb_bore:g} mm spindle; pinion key/clamp unresolved', True)
    bridge = layout['motor_bridge']; hz0 = a1 + .5
    for i, zc in enumerate(p['motor_bearing_centres_mm']):
        add(f'motor_bearing_{i}', ring(mx, my, zc-mb_w/2, zc+mb_w/2, mb_od, mb_bore), 'shaft',
            f'{support["motor_bearing"]["part"]} boundary envelope; opposed NJ pair, axial location unresolved')
    (bx0, bx1), (bz0, bz1) = bridge['x_mm'], bridge['z_mm']
    carrier = box((bx1-bx0, ey-2*wall, bz1-bz0), (bx0, wall, bz0)).union(
        ring(mx, my, hz0, bz0, bridge['housing_radius_mm'])).cut(ring(mx, my, hz0-1, bz1+1, mb_od))
    add('motor_bearing_carrier', carrier, 'plate', 'Side-wall-attached bridge with bearing housing; wall joints and stiffness unqualified')
    add('pinion', ring(mx, my, gear_z, gear_z+face, small_r+1, mb_bore), 'plate',
        f'{p["pinion_teeth"]}-tooth {p["pitch_mm"]} mm pitch envelope; tooth rating absent', True)

    # Drum side: two-ended 25 mm dead shaft (base boss to deck), bearings inside the winding core.
    db = layout['base_boss_radius_mm']; sp = layout['spacer_radius_mm']; hub = layout['hub_bore_radius_mm']
    db_lo = p['drum_bearing_centres_mm'][0]-db_w/2; db_hi = p['drum_bearing_centres_mm'][-1]+db_w/2
    if abs(db_lo-wind_lo) > 1e-6 or abs(db_hi-wind_hi) > 1e-6:
        raise ConfigError('drum bearings must span the winding core exactly in this layout')
    boss_top = 2*p['shaft_support_z_mm'][0] - base_t
    add('drum_base_boss', ring(dx, dy, base_t, boss_top, db, db_bore), 'plate', 'Lower shaft support; base flange/fastening unqualified')
    add('drum_dead_shaft', ring(dx, dy, base_t, deck_hi, db_bore), 'shaft', 'Two-ended 25 mm dead shaft; retention and fits unresolved')
    add('drum_shaft_spacer_lower', ring(dx, dy, boss_top, wind_lo, sp, db_bore), 'shaft', 'Locates lower bearing inner race; proposal')
    add('drum_shaft_spacer_upper', ring(dx, dy, wind_hi, deck_lo, sp, db_bore), 'shaft', 'Locates upper bearing inner race; proposal')
    for i, (zc, key) in enumerate(zip(p['drum_bearing_centres_mm'], ('drum_floating', 'drum_locating'))):
        add(f'drum_bearing_{i}', ring(dx, dy, zc-db_w/2, zc+db_w/2, db_od, db_bore), 'shaft',
            f'{support[key]["part"]} boundary envelope; outer race rotates with drum')
    drum = ring(dx, dy, wind_lo, wind_hi, core, db_od)
    drum = drum.union(ring(dx, dy, wind_lo-flange_t, wind_lo, flange_r, db_od))
    drum = drum.union(ring(dx, dy, wind_hi, wind_hi+flange_t, flange_r, db_od))
    drum = drum.union(ring(dx, dy, wind_hi+flange_t, gear_z, core, hub))
    add('drum', drum, 'plate', 'Thin-wall core around bearings; 2 mm flanges and hub need load/fatigue review', True)
    add('wound_rope_envelope', ring(dx, dy, wind_lo, wind_hi, core+ref['layers']*rope_d, core), 'black',
        'Occupied winding space only; crossovers and helix absent')
    wheel = ring(dx, dy, gear_z, gear_z+face, large_r+1, large_r-3).union(ring(dx, dy, gear_z, gear_z+face, 28, hub))
    for angle in range(0, 360, 60):
        wheel = wheel.union(box((large_r-3-26, 8, 3), (dx+27, dy-4, gear_z)).rotate((dx, dy, 0), (dx, dy, 1), angle))
    add('driven_wheel', wheel, 'plate', f'{p["wheel_teeth"]}-tooth envelope with six-spoke web; tooth geometry/rating absent', True)
    a = math.asin((large_r-small_r)/centre)
    for side in (-1, 1):
        nx, ny = -math.sin(a), side*math.cos(a)
        p1 = (mx+small_r*nx, my+small_r*ny); p2 = (dx+large_r*nx, dy+large_r*ny)
        pts = [(p1[0]+nx, p1[1]+ny), (p2[0]+nx, p2[1]+ny), (p2[0]-nx, p2[1]-ny), (p1[0]-nx, p1[1]-ny)]
        add(f'belt_span_{side}', cq.Workplane('XY').workplane(offset=gear_z).polyline(pts).close().extrude(face),
            'black', 'Straight belt envelope; wrap arcs omitted')
    (dk0, dk1) = layout['deck']['x_mm']
    add('deck', box((dk1-dk0, ey-2*wall, deck_hi-deck_lo), (dk0, wall, deck_lo)).cut(ring(dx, dy, deck_lo-1, deck_hi+1, db_bore)),
        'plate', 'Side-wall-attached deck: upper shaft support and electronics tray; plate/joint checks open')

    # Rope exit and guide toward +Y.
    rx0, rx1 = layout['rope_exit']['x_mm']; g = layout['guide']
    rope_keepout = box((rx1-rx0, ey+.5-(dy+5), wind_hi-wind_lo+1), (rx0, dy+5, wind_lo-.5))
    (gx0, gx1), (gy0, gy1), gh = g['carriage_x_mm'], g['carriage_y_mm'], g['carriage_height_mm']
    mid = (wind_lo+wind_hi)/2
    add('guide_carriage', box((gx1-gx0, gy1-gy0, gh), (gx0, gy0, mid-gh/2)), 'plate', 'Mid-travel; full sweep checked separately')
    add('guide_screw', ring(*g['screw_xy_mm'], *g['screw_z_mm'], 3), 'shaft', 'Proposed guide drive; synchronization and wear unqualified')
    guide_sweep = box((gx1-gx0, gy1-gy0, width-rope_d+gh), (gx0, gy0, wind_lo+rope_d/2-gh/2))

    # Power and electronics.
    sx, sy, sz = layout['supply_corner_mm']
    add('supply_envelope', box((supply['width_mm'], supply['length_mm'], supply['height_mm']), (sx, sy, sz)), 'electronics',
        'Sourced EPP-500-54 envelope; terminals, clearances and 25 CFM path not established')
    cell = support['cell']['values']; r = cell['diameter_mm']/2; count = 0
    for group in layout['cell_groups']:
        key = 'centres_yz_mm' if group['axis'] == 'x' else 'centres_xz_mm'
        for start in group['length_start_mm']:
            for u, v in group[key]:
                origin = (start, u, v) if group['axis'] == 'x' else (u, start, v)
                add(f'capacitor_{count:02}', cylinder(r, cell['length_mm'], origin, group['axis']), 'electronics',
                    f'{support["cell"]["part"]} body ({group["name"]} group); leads, insulation and balance boards additional')
                count += 1
    if count != p['cells_series']:
        raise ConfigError(f'R2 layout places {count} cells; proposal requires {p["cells_series"]}')
    for claim in layout['electrical_space_claims']:
        add(claim['name'], box(claim['size_mm'], claim['corner_mm']), 'electronics',
            'Unselected functional allocation; electrical/thermal clearances require verification')
    belt_length = 2*math.sqrt(centre**2-(large_r-small_r)**2) + math.pi*(large_r+small_r) + 2*(large_r-small_r)*a
    return objects, fidelity, dict(layout=layout, reference=ref, drum_axis=(dx, dy), rope_keepout=rope_keepout,
                                   guide_sweep=guide_sweep, belt_length_mm=belt_length,
                                   small_wrap_deg=(math.pi-2*a)*180/math.pi, proposal=p)


def check(objects, info):
    """Solid overlaps (tooth proxies excepted), envelope bounds and swept keepouts."""
    proxies = {frozenset((w, b)) for w in ('driven_wheel', 'pinion') for b in ('belt_span_-1', 'belt_span_1')}
    collisions = []
    for a, b in itertools.combinations(objects, 2):
        if frozenset((a.name, b.name)) in proxies: continue
        if volume := overlaps(a.shape, b.shape):
            collisions.append({'a': a.name, 'b': b.name, 'volume_mm3': volume})
    bounds = [o.name for o in objects if any(
        getattr(bb := o.shape.val().BoundingBox(), ax+'min') < -1e-6 or getattr(bb, ax+'max') > lim+1e-6
        for ax, lim in zip('xyz', info['layout']['envelope_mm']))]
    keepouts = {name: [{'part': o.name, 'volume_mm3': v} for o in objects
                       if not o.name.startswith(('drum', 'guide', 'wound_rope')) and (v := overlaps(o.shape, info[key]))]
                for name, key in (('rope_path', 'rope_keepout'), ('guide_sweep', 'guide_sweep'))}
    return collisions, bounds, keepouts


def plot_layout(objects, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(13, 7))
    axes = [fig.add_subplot(121, projection='3d'), fig.add_subplot(122, projection='3d')]
    for obj in objects:
        if obj.name in ('enclosure_skin', 'base', 'deck'): continue
        vertices, triangles = obj.shape.val().tessellate(1.)
        polys = [[(vertices[j].x, vertices[j].y, vertices[j].z) for j in t] for t in triangles]
        color = ('#467c91' if obj.name.startswith('capacitor_') else '#62836c' if obj.material == 'electronics'
                 else '#aa6a3b' if obj.material == 'motor' else '#353b40' if obj.material == 'black' else '#a8adb0')
        for ax in axes:
            ax.add_collection3d(Poly3DCollection(polys, facecolor=color, edgecolor='none',
                                                 alpha=.2 if obj.name == 'wound_rope_envelope' else 1))
    for ax, title, view in zip(axes, ('Mechanism side', 'End bay: supply, bank, inlet'), ((26, -60), (22, 120))):
        ax.set(xlim=(0, 323), ylim=(0, 139), zlim=(0, 100), xlabel='X mm', ylabel='Y mm', zlabel='Z mm', title=title)
        ax.set_box_aspect((323, 139, 100)); ax.view_init(*view); ax.set_proj_type('ortho'); ax.tick_params(labelsize=7)
    fig.suptitle('R2 compact integration (323 × 139 × 100 mm)', fontsize=15)
    fig.text(.5, .06, 'Blue: TV cells · Green: electrical claims · Orange: motor · Dark: belt/rope · Grey: structure (skin, base and deck hidden)',
             ha='center', fontsize=9)
    fig.text(.5, .025, 'REVISE — wiring, trays, retention, electrical clearances and cooling remain incomplete.', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .07, 1, .94)); fig.savefig(path, dpi=170); plt.close(fig)


def generate(root=Path('.')):
    root = Path(root); cq = _cq(); digest = package_fingerprint(root)
    objects, fidelity, info = build(root)
    out = root/'build/cad'; out.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(assemble(objects).toCompound(), str(out/'r2_integration.step'))
    for tag, selected in (('full', objects), ('cutaway', [o for o in objects if o.name not in ('enclosure_skin', 'deck')])):
        path = out/f'r2_integration_{tag}.glb'; assemble(selected).save(str(path), exportType='GLTF'); gltf_to_metres_y_up(path)
    collisions, bounds, keepouts = check(objects, info)
    _, parts = load_coupled(root)
    inertia = inertia_properties(objects, info, parts)
    result = {'fingerprint': digest, 'assessment': 'REVISE; unqualified integration experiment',
              'envelope_mm': info['layout']['envelope_mm'], 'ratio': info['reference']['ratio'],
              'part_count': len(objects), 'out_of_bounds': bounds, 'collisions': collisions, 'keepout_collisions': keepouts,
              'inertia': inertia, 'routing_length_m': info['layout']['routing_length_m'],
              'belt_length_mm': info['belt_length_mm'], 'pinion_wrap_deg': info['small_wrap_deg'],
              'unplaced_required_functions': ['force transducer and overload path', 'stop actuator', 'mount retention and sensing',
                  'external peer connector', 'encoder and winding sensor detail', 'positive shaft/bearing retention',
                  'connector bodies and pinouts', 'mains/DC insulation and airflow keepouts', 'wiring, bus bars and cell leads',
                  'electronics trays and standoffs', 'belt tensioner'],
              'parts': fidelity, 'limits': info['layout']['notes']}
    (root/'reports/r2_package.json').write_text(json.dumps(result, indent=2)+'\n')
    plot_layout(objects, root/'reports/figures/r2_package.png')
    i = inertia
    lines = ['# R2 compact integration', '', f'Fingerprint: `{digest}`', '', '![R2 CAD views](figures/r2_package.png)', '',
             '**REVISE. Space claim, not a qualified assembly.** R2 combines the [support revision](support_revision.md) and '
             '[power revision](revision_power.md): 5:1 belt (24/120 × 3 mm), opposed NJ 202 motor bearings in a '
             'wall-attached bridge, NU205/NUP205 drum bearings inside the winding core on a 25 mm shaft supported by a '
             'base boss and a wall-attached deck, side (+Y) rope exit, EPP-500-54 flat in the end bay, 20 TV cells in '
             'three groups, ODrive Pro and Regen Clamp on the deck.', '',
             f'Body target {result["envelope_mm"]} mm; {len(objects)} parts; out of bounds: {bounds or "none"}; '
             f'unintended solid overlaps: {len(collisions)}.', '',
             f'Drum-referred inertia: {i["complete_known_reflected_inertia_kg_m2"]:.6f} kg m² total at 5:1 '
             f'(drum + wheel {i["drum_and_wheel_inertia_kg_m2"]:.6f}; motor-side additions '
             f'{i["motor_adapter_spindle_pinion_inertia_kg_m2"]:.6f} at motor speed; catalog rotor included once). '
             'Aluminium/steel densities 2700/7850 kg/m³ assumed.', '',
             f'Open-belt length {info["belt_length_mm"]:.1f} mm; pinion wrap {info["small_wrap_deg"]:.1f}°. '
             f'Nominal routing {info["layout"]["routing_length_m"]} m: {info["layout"]["routing_basis"]}', '',
             '## Collision evidence', '']
    lines += [f'- {c["a"]} × {c["b"]}: {c["volume_mm3"]:.2f} mm³' for c in collisions] or ['No unintended solid overlaps.']
    for name, values in keepouts.items():
        lines += ['', f'{name}: ' + (str(values) if values else 'no listed solid intersection; contact design unqualified.')]
    lines += ['', '## Fidelity', '', '| Part | Evidence/detail |', '|---|---|']
    lines += [f'| {n} | {d} |' for n, d in fidelity.items()]
    lines += ['', '## Remaining requirements', ''] + ['- '+n for n in result['limits']]
    lines += ['', 'Not yet represented: ' + ', '.join(result['unplaced_required_functions']) + '.', '',
              'Reproduce: `make r2-package`. STEP/GLB: `build/cad/r2_integration.step`, `r2_integration_{full,cutaway}.glb`.', '']
    (root/'reports/r2_package.md').write_text('\n'.join(lines))
    return result


if __name__ == '__main__':
    r = generate()
    print(f'R2 package: {r["part_count"]} parts; collisions {len(r["collisions"])}; out of bounds {r["out_of_bounds"]}; '
          f'keepouts {sum(len(v) for v in r["keepout_collisions"].values())}; '
          f'J {r["inertia"]["complete_known_reflected_inertia_kg_m2"]:.6f}')
