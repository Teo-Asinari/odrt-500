"""Geometry evidence checks, not a strength or electrical qualification."""
import itertools
import math

import pytest

pytest.importorskip('cadquery')

from conftest import REPO
from odrt.compact_package import build, overlaps


@pytest.fixture(scope='module')
def geometry():
    return build(REPO)


def test_complete_space_claim_stays_inside_owner_body_and_has_no_solid_clashes(geometry):
    parts,_,info=geometry
    for part in parts:
        bb=part.shape.val().BoundingBox()
        for axis,limit in zip('xyz',(323,139,100)):
            assert getattr(bb,axis+'min')>=-1e-6,part.name
            assert getattr(bb,axis+'max')<=limit+1e-6,part.name
    tooth_proxies={frozenset((wheel,belt)) for wheel in ('driven_wheel','pinion')
                   for belt in ('belt_span_-1','belt_span_1')}
    for a,b in itertools.combinations(parts,2):
        if frozenset((a.name,b.name)) in tooth_proxies:continue
        assert overlaps(a.shape,b.shape)==0,(a.name,b.name)


def test_rope_and_guide_full_swept_space_clear_static_components(geometry):
    parts,_,info=geometry
    for key in ('rope_keepout','guide_sweep'):
        for part in parts:
            if part.name.startswith(('drum','guide','wound_rope')):continue
            assert overlaps(info[key],part.shape)==0,(key,part.name)


def test_motor_carrier_adds_real_reflected_inertia_not_just_catalog_rotor(geometry):
    import cadquery as cq
    parts,_,info=geometry
    adapter=next(part.shape.val() for part in parts if part.name=='motor_rotor_adapter')
    # Solid 50 mm-radius, 5 mm-thick aluminium disk: independent analytic check.
    mass=2700*math.pi*.05**2*.005
    expected=.5*mass*.05**2
    actual=cq.Shape.matrixOfInertia(adapter)[2][2]*2700*1e-15
    assert actual==pytest.approx(expected,rel=1e-9)
    assert actual*info['reference']['ratio']**2>.004
