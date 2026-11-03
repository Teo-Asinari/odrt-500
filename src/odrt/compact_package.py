"""Compact integration experiment with explicit collisions and fidelity labels.

Run python -m odrt.compact_package. A geometrically fitting space claim cannot
establish electrical isolation, cooling, strength, rope life or feasibility.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path

from odrt.cad import Part, _cq, assemble, gltf_to_metres_y_up
from odrt.config import load_yaml
from odrt.coupled import fingerprint, load_coupled


def build(root=Path('.')):
    root=Path(root);cq=_cq()
    layout=load_yaml(root/'configs/compact_package.yaml')
    cfg,parts=load_coupled(root)
    compact=load_yaml(root/'data/compact_buffer.yaml')['documented']
    ref=cfg['reference']; motor=parts[ref['motor']]['values'];supply=parts[ref['supply']]['values']
    mx,my=layout['motor_axis_xy_mm'];dx,dy=layout['drum_axis_xy_mm']
    rope_diameter=parts[ref['rope']]['values']['diameter_mm']
    radius=ref['core_radius_mm'];width=ref['turns_per_layer']*rope_diameter
    thickness=layout['drum_flange_thickness_mm'];bottom=layout['drum_bottom_mm']
    pitch=layout['belt_pitch_mm'];small_r=pitch*layout['pinion_teeth']/(2*math.pi)
    large_r=small_r*ref['ratio'];face=layout['pulley_face_mm'];gear_z=layout['pulley_bottom_mm']
    objects=[]; fidelity={}

    def add(name,shape,material,detail,moving=False):
        objects.append(Part(name,shape,material,moving));fidelity[name]=detail
        return shape

    def box(size,corner):
        return cq.Workplane('XY').box(*size,centered=False).translate(corner)

    def ring(x,y,z,outer,inner,height):
        wp=cq.Workplane('XY').workplane(offset=z).center(x,y).circle(outer)
        if inner:wp=wp.circle(inner)
        return wp.extrude(height)

    add('base',box((323,139,2),(0,0,0)),'plate','Proposed structural base; mounting joints unqualified')
    skin=box((323,139,98),(0,0,2)).cut(box((319,135,96),(2,2,2)))
    skin=skin.cut(box((55,3,30),(184,-.5,46))).cut(box((3,10,35),(320.5,99,43.5)))
    add('enclosure_skin',skin,'plate','2 mm skin with inlet and moving-rope slots; sealing and attachment unresolved')
    add('motor_pedestal',ring(mx,my,2,motor['diameter_mm']/2,0,6),'plate','Carrier interface and rotor/stator attachment unresolved')
    add('motor_envelope',ring(mx,my,8,motor['diameter_mm']/2,0,motor['length_mm']),'motor','Sourced outer envelope only; internal rotor/stator geometry absent')
    add('motor_rotor_adapter',ring(mx,my,36,50,0,5),'plate','Proposed rotating carrier; actual motor mating geometry unresolved',True)
    add('motor_spindle',ring(mx,my,41,5,0,53),'shaft','Proposed 10 mm spindle and positive-drive interface unresolved',True)
    for index,z in enumerate((60,68)):
        add(f'motor_bearing_{index}',ring(mx,my,z,13,5,8),'shaft','NSK 6000 boundary envelope; ball/race detail omitted')
    add('motor_bearing_housing',ring(mx,my,59,17,13,17),'plate','Bearing seat/retention not detailed')
    carrier=box((116,69,2),(7,35,76)).cut(ring(mx,my,75,13,0,4))
    add('motor_carrier_bridge',carrier,'plate','Connected load path proposal; plate and joint checks open')
    for index,(x,y) in enumerate(((7,35),(123,35),(7,104),(123,104))):
        add(f'motor_post_{index}',ring(x,y,2,3,0,74),'shaft','Proposed stationary post; fasteners omitted')
    bore=layout['drum_bore_radius_mm'];flange=layout['drum_flange_radius_mm']
    drum=ring(dx,dy,bottom,radius,bore,width+2*thickness)
    drum=drum.union(ring(dx,dy,bottom,flange,bore,thickness))
    drum=drum.union(ring(dx,dy,bottom+thickness+width,flange,bore,thickness))
    drum=drum.union(ring(dx,dy,bottom+width+thickness,26,12.75,gear_z-bottom-width-thickness))
    add('drum',drum,'plate','Hollow core and flanges match winding width; 2 mm flanges need load/fatigue review',True)
    add('wound_rope_envelope',ring(dx,dy,bottom+thickness,radius+ref['layers']*rope_diameter,radius,width),
        'black','Occupied winding space only; crossovers and actual helical rope geometry absent')
    for index,z in enumerate((46,64)):
        add(f'drum_bearing_{index}',ring(dx,dy,z,23.5,12.5,12),'shaft','NSK 6005 envelope; shaft stationary and outer race rotates with drum')
    add('drum_dead_shaft',ring(dx,dy,46,12.5,0,52),'shaft','Top-supported 25 mm dead shaft; retention and cantilever joint unresolved')
    top=box((103,122,2),(129,9,96)).cut(ring(dx,dy,95,12.5,0,4))
    add('drum_top_bridge',top,'plate','Connected to shaft/post proposal; 2 mm thickness unqualified')
    for index,(x,y) in enumerate(((132,12),(228,35),(132,127),(228,127))):
        add(f'drum_post_{index}',ring(x,y,2,3,0,94),'shaft','Proposed shaft-support post and fasteners')
    wheel=ring(dx,dy,gear_z,large_r+1,large_r-3,face)
    wheel=wheel.union(ring(dx,dy,gear_z,26,12.75,face))
    for angle in range(0,360,60):
        spoke=box((large_r-21,8,3),(dx+22,dy-4,gear_z)).rotate((dx,dy,0),(dx,dy,1),angle)
        wheel=wheel.union(spoke)
    add('driven_wheel',wheel,'plate','120-tooth 3 mm pitch envelope and lightweight web; tooth geometry/rating absent',True)
    add('pinion',ring(mx,my,gear_z,small_r+1,5,face),'plate','20-tooth 3 mm pitch envelope; bore fits spindle; rating/key unresolved',True)
    # Exact external-tangent belt envelope (no teeth, stock length or tensioner claim).
    centre=math.hypot(dx-mx,dy-my);a=math.asin((large_r-small_r)/centre)
    tangent_points=[]
    for side in (-1,1):
        normal=(-math.sin(a),side*math.cos(a))
        p1=(mx+small_r*normal[0],my+small_r*normal[1]);p2=(dx+large_r*normal[0],dy+large_r*normal[1])
        nx,ny=normal
        points=[(p1[0]+nx,p1[1]+ny),(p2[0]+nx,p2[1]+ny),
                (p2[0]-nx,p2[1]-ny),(p1[0]-nx,p1[1]-ny)]
        tangent_points.append((p1,p2))
        belt=cq.Workplane('XY').workplane(offset=gear_z).polyline(points).close().extrude(face)
        add(f'belt_span_{side}',belt,'black','Straight belt envelope only; wrap arcs omitted')
    add('supply_envelope',box((supply['width_mm'],supply['length_mm'],supply['height_mm']),(137,6,3)),
        'electronics','Sourced EPP-500 envelope; mains terminals, underside clearance and 25 CFM ducting not established')
    add('supply_partition_claim',box((80,129,1),(135,5,43)),'plate','Illustrative barrier only; NOT rated isolation clearance')
    for index in range(22):
        if index<20:
            layer,row=divmod(index,5);y,z=12+19*row,14.5+20*layer
        else:y,z=125,12+19*(index-20)
        cell=cq.Workplane('YZ').workplane(offset=239).center(y,z).circle(compact['diameter_max_mm']/2).extrude(compact['length_max_mm'])
        add(f'capacitor_{index:02}',cell,'electronics','Eaton maximum body envelope; lead bend, insulation and balance/protection boards additional')
    for entry in layout['electrical_space_claims']:
        add(entry['name'],box(entry['size_mm'],entry['corner_mm']),'electronics',
            'Unselected functional allocation; footprint/height and all electrical/thermal clearances require verification')
    # A traversing guide concept, intentionally exposed as unqualified contact geometry.
    add('guide_screw',ring(265,118,41,3,0,42),'shaft','Proposed guide drive; actuator synchronization and wear unqualified')
    add('guide_carriage',box((20,16,6),(255,99,58)),'plate','Mid-travel only; entire 30 mm swept volume checked separately')
    guide_sweep=box((20,16,36),(255,99,43))
    rope_keepout=box((148,10,width+1),(175,99,bottom+thickness-.5))
    # Rope contact detail is not faked: keepout/swept checks retain missing design evidence.
    return objects,fidelity,dict(layout=layout,reference=ref,guide_sweep=guide_sweep,rope_keepout=rope_keepout,
                                drum_axis=(dx,dy),belt_length_mm=2*math.sqrt(centre**2-(large_r-small_r)**2)
                                +math.pi*(large_r+small_r)+2*(large_r-small_r)*a,
                                small_wrap_deg=(math.pi-2*a)*180/math.pi)


def overlaps(a,b,tolerance=1.):
    aa,bb=a.val().BoundingBox(),b.val().BoundingBox()
    if any(min(getattr(aa,axis+'max'),getattr(bb,axis+'max')) <=
           max(getattr(aa,axis+'min'),getattr(bb,axis+'min'))+1e-6 for axis in 'xyz'):
        return 0.
    volume=a.val().intersect(b.val()).Volume()
    return volume if volume>tolerance else 0.


def plot_layout(objects,path):
    """Inspect the actual CAD tessellation; colors encode fidelity/part groups."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(13,7))
    axes=[fig.add_subplot(121,projection='3d'),fig.add_subplot(122,projection='3d')]
    for obj in objects:
        if obj.name=='enclosure_skin':continue
        vertices,triangles=obj.shape.val().tessellate(1.)
        polygons=[[(vertices[j].x,vertices[j].y,vertices[j].z) for j in triangle] for triangle in triangles]
        color=('#467c91' if obj.name.startswith('capacitor_') else '#62836c' if obj.material=='electronics'
               else '#aa6a3b' if obj.material=='motor' else '#353b40' if obj.material=='black' else '#a8adb0')
        alpha=.2 if obj.name=='wound_rope_envelope' else 1
        for ax in axes:
            ax.add_collection3d(Poly3DCollection(polygons,facecolor=color,edgecolor='none',alpha=alpha))
    for ax,title,view in zip(axes,('Cutaway integration','Opposite view: supply under drum'),((26,-60),(22,120))):
        ax.set(xlim=(0,323),ylim=(0,139),zlim=(0,100),xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title=title)
        ax.set_box_aspect((323,139,100));ax.view_init(*view);ax.set_proj_type('ortho')
        ax.tick_params(labelsize=7)
    fig.suptitle('323 × 139 × 100 mm compact integration experiment',fontsize=15)
    fig.text(.5,.06,'Blue: capacitor bodies · Green: electrical space claims · Orange: motor envelope · Grey: proposed structure',ha='center',fontsize=9)
    fig.text(.5,.025,'REVISE — wiring, sensors, retention, electrical clearances and cooling remain incomplete.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.07,1,.94));fig.savefig(path,dpi=170);plt.close(fig)


def inertia_properties(objects,info,parts):
    """Sum CAD inertias about their actual axes, then refer motor additions to drum."""
    cq=_cq()
    dx,dy=info['drum_axis'];moving_inertia=0.;motor_added_inertia=0.
    mx,my=info['layout']['motor_axis_xy_mm']
    for obj in objects:
        if obj.name not in ('drum','driven_wheel','motor_rotor_adapter','motor_spindle','pinion'):continue
        shape=obj.shape.val();com=shape.Center();tensor=cq.Shape.matrixOfInertia(shape)
        on_drum=obj.name in ('drum','driven_wheel')
        ax,ay=(dx,dy) if on_drum else (mx,my)
        density=7850 if obj.material=='shaft' else 2700
        inertia=(tensor[2][2]+shape.Volume()*((com.x-ax)**2+(com.y-ay)**2))*density*1e-15
        if on_drum:moving_inertia+=inertia
        else:motor_added_inertia+=inertia
    motor_j=parts[info['reference']['motor']]['values']['inertia_kg_m2']
    equivalent=moving_inertia+info['reference']['ratio']**2*motor_added_inertia
    return dict(drum_and_wheel_inertia_kg_m2=moving_inertia,
                motor_adapter_spindle_pinion_inertia_kg_m2=motor_added_inertia,
                equivalent_added_drum_inertia_kg_m2=equivalent,
                complete_known_reflected_inertia_kg_m2=equivalent+info['reference']['ratio']**2*motor_j)


def generate(root=Path('.')):
    root=Path(root);cq=_cq();objects,fidelity,info=build(root)
    build_dir=root/'build/cad';build_dir.mkdir(parents=True,exist_ok=True)
    assembly=assemble(objects)
    cq.exporters.export(assembly.toCompound(),str(build_dir/'compact_integration.step'))
    for tag,selected in (('full',objects),('cutaway',[v for v in objects if v.name!='enclosure_skin'])):
        path=build_dir/f'compact_integration_{tag}.glb'
        assemble(selected).save(str(path),exportType='GLTF')
        gltf_to_metres_y_up(path)
    collisions=[]
    intended={frozenset((wheel,belt)) for wheel in ('driven_wheel','pinion') for belt in ('belt_span_-1','belt_span_1')}
    envelope_contacts=[]
    for a,b in itertools.combinations(objects,2):
        volume=overlaps(a.shape,b.shape)
        if volume:
            row={'a':a.name,'b':b.name,'volume_mm3':volume}
            if frozenset((a.name,b.name)) in intended:
                envelope_contacts.append({**row,'basis':'Pitch/tooth engagement proxies overlap; detailed belt/teeth absent'})
            else:collisions.append(row)
    bounds=[]
    for obj in objects:
        bb=obj.shape.val().BoundingBox()
        if any(getattr(bb,axis+'min') < -1e-6 or getattr(bb,axis+'max') > limit+1e-6
               for axis,limit in zip('xyz',info['layout']['envelope_mm'])):
            bounds.append(obj.name)
    keepouts={}
    for name,shape in (('rope_path',info['rope_keepout']),('guide_sweep',info['guide_sweep'])):
        keepouts[name]=[{'part':obj.name,'volume_mm3':volume} for obj in objects
                        if not obj.name.startswith(('drum','guide','wound_rope'))
                        and (volume:=overlaps(obj.shape,shape))]
    cfg,parts=load_coupled(root)
    inertia=inertia_properties(objects,info,parts)
    moving_inertia=inertia['drum_and_wheel_inertia_kg_m2']
    motor_added_inertia=inertia['motor_adapter_spindle_pinion_inertia_kg_m2']
    total_j=inertia['complete_known_reflected_inertia_kg_m2']
    digest=hashlib.sha256(fingerprint(root).encode())
    for source in ('configs/compact_package.yaml','data/compact_buffer.yaml'):
        digest.update((root/source).read_bytes())
    digest.update(Path(__file__).read_bytes())
    result={'fingerprint':digest.hexdigest(),'assessment':'REVISE; unqualified integration experiment',
            'envelope_mm':info['layout']['envelope_mm'],'part_count':len(objects),'out_of_bounds':bounds,
            'collisions':collisions,'keepout_collisions':keepouts,'drum_and_wheel_inertia_kg_m2':moving_inertia,
            'intentional_pitch_envelope_contacts':envelope_contacts,
            'motor_adapter_spindle_pinion_inertia_kg_m2':motor_added_inertia,
            'complete_known_reflected_inertia_kg_m2':total_j,
            'equivalent_added_drum_inertia_kg_m2':inertia['equivalent_added_drum_inertia_kg_m2'],
            'inertia_density_assumptions_kg_m3':{'aluminium':2700,'steel':7850},
            'unplaced_required_functions':['force transducer and overload path','stop actuator','mount retention and state sensing',
                'external peer connector','encoder and winding sensor detail','positive shaft/bearing retention',
                'connector bodies and pinouts','mains/DC insulation and airflow keepouts','wiring and formed capacitor leads'],
            'coupled_reference_drum_inertia_kg_m2':info['reference']['drum_inertia_kg_m2'],
            'belt_length_mm':info['belt_length_mm'],'pinion_wrap_deg':info['small_wrap_deg'],
            'parts':fidelity,'limits':info['layout']['notes']}
    (root/'reports/compact_package.json').write_text(json.dumps(result,indent=2)+'\n')
    plot_layout(objects,root/'reports/figures/compact_package.png')
    lines=['# Compact integration experiment','',f'Fingerprint: `{result["fingerprint"]}`','',
           '![CAD integration views](figures/compact_package.png)','',
           '**REVISE. This is an integration experiment, not a qualified compact assembly.** '
           'It rotates the shafts vertically, stacks the supply below the drum, uses a top-supported dead shaft '
           'and reserves an end bay for the compact capacitor alternative. The verified coupled reference still '
           'uses the large bank; this alternative is not silently substituted.','',
           f'Body target: {result["envelope_mm"]} mm. Parts: {len(objects)}. '
           f'Out of bounds: {bounds or "none"}. Solid overlaps: {len(collisions)}.','',
           f'CAD drum + wheel aluminium inertia: {moving_inertia:.6g} kg m², versus '
           f'{info["reference"]["drum_inertia_kg_m2"]:.6g} in the coupled reference. '
           'Rope winding and bearing rotating masses are additional; this mismatch must be reconciled before '
           'calling the CAD and simulation one design.','',
           f'Motor adapter + spindle + pinion add {motor_added_inertia:.6g} kg m² at motor speed. '
           f'Total known reflected inertia including the catalog rotor is {total_j:.6g} kg m². '
           'This uses assumed aluminium/steel densities of 2700/7850 kg/m³. '
           'Carrier inertia is additional to the bare motor rotor and must not be omitted.','',
           f'Open-belt geometric length: {info["belt_length_mm"]:.2f} mm; pinion wrap {info["small_wrap_deg"]:.1f}°. '
           'No stock belt, tooth load rating, fatigue life or tensioner range is qualified.','',
           '## Collision evidence','', '| Part A | Part B | Overlap mm³ |','|---|---|---:|']
    lines += [f'| {v["a"]} | {v["b"]} | {v["volume_mm3"]:.2f} |' for v in collisions]
    for name,values in keepouts.items():
        lines += ['',f'### {name}','',str(values) if values else 'No listed solid intersection; clearances/contact design remain unqualified.']
    lines += ['','## Fidelity','', '| Part | Evidence/detail |','|---|---|']
    lines += [f'| {name} | {detail} |' for name,detail in fidelity.items()]
    lines += ['','## Remaining requirements','']+['- '+note for note in result['limits']]
    lines += ['','Required functions not yet represented by complete geometry: '+', '.join(result['unplaced_required_functions'])+'.']
    lines += ['','Motor carrier → posts → base and drum → bearings → dead shaft → top bridge → posts → base '
              'are connected proposed load paths. Strength, joints, positive retention, board/adapter load '
              'transfer, electrical isolation, cooling and installation clearances remain unqualified. '
              'No bare overlap check establishes these properties.','',
              'Reproduce: `.venv/bin/python -m odrt.compact_package`. STEP: `build/cad/compact_integration.step`; '
              'GLBs: `compact_integration_full.glb` and `compact_integration_cutaway.glb` in the same directory.','']
    (root/'reports/compact_package.md').write_text('\n'.join(lines))
    return result


if __name__=='__main__':
    generate()
