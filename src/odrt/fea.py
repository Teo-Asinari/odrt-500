"""WP4 FEA: side plate under bearing load (gmsh + scikit-fem, quadratic tetrahedra).

The brief names CalculiX; it is not pip-installable, so this uses a pure-Python
solver that runs headlessly from a clean venv (R-13). Same physics: small-strain
linear elasticity. Plate: thickness t along X, depth along Y, height along Z,
bottom face fixed (bolted/welded to the base plate), bearing bore loaded toward
+Y (the cable pull direction) with a cosine pressure over the loaded half.
"""
from __future__ import annotations

import math

import numpy as np


def _mesh(dims: dict, h_mm: float):
    import gmsh
    from skfem import MeshTet
    t, depth = dims["plate_t"], dims["plate_depth"]
    height = dims["plate_h"] - dims["base_t"]
    zc = dims["axis_z"] - dims["base_t"]
    r = dims["bearing_od"] / 2
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.option.setNumber("Mesh.RandomSeed", 1)
        box = gmsh.model.occ.addBox(0, -depth / 2, 0, t, depth, height)
        hole = gmsh.model.occ.addCylinder(-1, 0, zc, t + 2, 0, 0, r)
        gmsh.model.occ.cut([(3, box)], [(3, hole)])
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMax", h_mm)
        gmsh.option.setNumber("Mesh.MeshSizeMin", h_mm / 3)
        gmsh.model.mesh.generate(3)
        tags, coords, _ = gmsh.model.mesh.getNodes()
        types, _, conn = gmsh.model.mesh.getElements(3)
        tet = conn[list(types).index(4)].reshape(-1, 4)
    finally:
        gmsh.finalize()
    index = {int(tag): i for i, tag in enumerate(tags)}
    p = coords.reshape(-1, 3).T * 1e-3  # metres
    t_idx = np.vectorize(index.get)(tet).T
    used = np.unique(t_idx)
    remap = -np.ones(p.shape[1], dtype=int)
    remap[used] = np.arange(len(used))
    return MeshTet(p[:, used], remap[t_idx]), zc * 1e-3, r * 1e-3


def side_plate(dims: dict, force_n: float, youngs_pa: float, poisson: float, h_mm: float) -> dict:
    from skfem import Basis, ElementTetP2, ElementVectorH1, FacetBasis, LinearForm, asm, condense, solve
    from skfem.helpers import sym_grad
    from skfem.models.elasticity import lame_parameters, linear_elasticity, linear_stress

    m, zc, r = _mesh(dims, h_mm)
    t = dims["plate_t"] * 1e-3
    e = ElementVectorH1(ElementTetP2())
    basis = Basis(m, e, intorder=3)
    lam, mu = lame_parameters(youngs_pa, poisson)
    K = asm(linear_elasticity(lam, mu), basis)

    mid = m.p[:, m.facets].mean(axis=1)
    bottom = np.flatnonzero(np.isclose(mid[2], 0.0, atol=1e-9) & np.isin(np.arange(m.facets.shape[1]), m.boundary_facets()))
    # bore facets: all three vertices on the cylinder (excludes face triangles touching the hole edge)
    vr = np.hypot(m.p[1, m.facets], m.p[2, m.facets] - zc)
    bore = np.intersect1d(np.flatnonzero(np.all(np.abs(vr - r) < 1e-6, axis=0)), m.boundary_facets())
    p0 = 2 * force_n / (math.pi * r * t)  # cosine pressure resultant equals force_n

    @LinearForm
    def bearing(v, w):
        y, z = w.x[1], w.x[2] - zc
        rr = np.hypot(y, z)
        cos, sin = y / rr, z / rr
        p = p0 * np.clip(cos, 0.0, None)  # radial pressure on the half facing +Y
        return p * (cos * v[1] + sin * v[2])

    f = asm(bearing, FacetBasis(m, e, facets=bore, intorder=4))
    unit_y = basis.zeros()
    unit_y[basis.nodal_dofs[1]] = 1.0
    unit_y[basis.edge_dofs[1]] = 1.0  # P2: a constant field is 1 at every node incl. edge midpoints
    fixed = basis.get_dofs(bottom).all()
    u = solve(*condense(K, f, D=fixed))

    w = basis.interpolate(u)
    s = linear_stress(lam, mu)(sym_grad(w))
    vm = np.sqrt(0.5 * ((s[0, 0] - s[1, 1]) ** 2 + (s[1, 1] - s[2, 2]) ** 2 + (s[2, 2] - s[0, 0]) ** 2)
                 + 3 * (s[0, 1] ** 2 + s[1, 2] ** 2 + s[0, 2] ** 2))
    xq = basis.mapping.F(basis.X)  # quadrature points, shape (3, elements, points)
    near_support = xq[2] < 0.005   # within 5 mm of the fixed edge: contains the clamp singularity
    disp = u[basis.nodal_dofs].reshape(3, -1) if basis.nodal_dofs.size else u.reshape(3, -1)
    height = (dims["plate_h"] - dims["base_t"]) * 1e-3
    depth = dims["plate_depth"] * 1e-3
    hand = 6 * force_n * zc / (t * depth**2)  # in-plane cantilever bending at the base
    return {
        "mesh_size_mm": h_mm,
        "elements": int(m.t.shape[1]),
        "dofs": int(K.shape[0]),
        "applied_force_n": float(f @ unit_y),
        "bore_facets": int(len(bore)),
        "max_displacement_mm": float(np.max(np.linalg.norm(disp, axis=0)) * 1e3),
        "max_von_mises_mpa": float(np.max(vm) / 1e6),
        "max_von_mises_away_from_support_mpa": float(np.max(np.where(near_support, 0.0, vm)) / 1e6),
        "hand_calc_base_bending_mpa": hand / 1e6,
        "plate_height_mm": height * 1e3,
    }
