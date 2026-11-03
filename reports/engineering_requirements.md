# Measurable engineering criteria

Input hash: `35846e129647a9a5e8a83db06e0eb4c9ef95b347b5b1e27bc151fb441ca738ab`

Owner decisions, proposed design screens and numerical verification criteria remain distinct. Provisional force/error/structural thresholds are not approved human-use safety limits.

| Criterion | Value (units in ID) | Origin | Basis | Acceptance evidence |
|---|---:|---|---|---|
| force_peak_lbf | 250 | owner | ADR-002 | bounded coupled scenario with ratings and thermal limits |
| units | 2 | owner | ADR-002 | independent supplies and asymmetric fault simulation |
| usable_stroke_m | 2.0 | provisional | R-05 upper-end target | winding capacity with dead turns and travel limits |
| peak_heavy_speed_m_s | 0.95 | provisional | A-007 | torque-speed-voltage envelope and heavy-tempo scenario |
| unit_volume_l_max | 4.4897 | owner | ADR-003 VOLTRA-sized body envelope | actual packaged enclosure bounding volume plus all three dimensional limits |
| unit_length_mm_max | 323 | owner | ADR-003 | packaged body bounding box including all internal systems |
| unit_width_mm_max | 139 | owner | ADR-003 | packaged body bounding box; orientation may be changed |
| unit_height_mm_max | 100 | owner | ADR-003 | packaged body bounding box; report external cord and connector clearances separately |
| unit_mass_kg_max | 5.8 | provisional | VOLTRA published comparison benchmark not an owner-approved limit | full parts and structure mass with unknowns explicit |
| tracking_rms_fraction_max | 0.05 | provisional | engineering comparison metric pending human-factors review | settled RMS error normalized by max(command RMS and absolute floor) |
| tracking_absolute_floor_n | 2 | provisional | avoid misleading relative errors near zero; not a safety limit | report absolute and relative errors separately |
| normal_overshoot_fraction_max | 0.1 | provisional | comparative engineering criterion; specialist review required | maximum settled normal-operation force above command |
| rope_design_factor | 5 | provisional | retained A-018 screen; dynamic/human-interactive use requires specialist factor review | compare documented spliced strength with maximum modeled transient |
| fatigue_cycles_target | 1000000 | provisional | lifetime comparison target pending duty/retirement review | rope supplier bend-fatigue data or controlled test; strength alone cannot satisfy |
| energy_residual_fraction_max | 0.005 | verification | numerical acceptance proposal | independent full-system input minus storage/loss/work ledger |
| convergence_normal_fraction_max | 0.02 | verification | numerical acceptance proposal | dt dt/2 dt/4 refinement of force motion voltage temperature and energy |
| convergence_fault_fraction_max | 0.05 | verification | numerical acceptance proposal for transient peaks | dt dt/2 dt/4 including fault event alignment |
| retail_per_unit_usd | 500 | owner | R-12 aspirational hypothesis | complete preliminary BOM assembly test overhead warranty and channel model |
| mount_deflection_mm_max | 2 | provisional | existing board criterion A-026 | symmetric and asymmetric mount/board load cases including joints |
| acoustic_db_a_at_1m_max | 55 | provisional | apartment-compatible comparison target; no measured source available | later calibrated acoustic test; simulation alone cannot close |

Duty-cycle definitions remain versioned in `configs/scenarios.yaml`: the complete heavy set, 3 s top holds, slow pulls and endurance session must be evaluated, not just a short representative window. Mounting must cover board, wall and rack load paths, arbitrary pull direction and asymmetry; a door adapter has no established capacity. Mains operation and independent local safety follow ADR-002. Noise, life and perceptual smoothness cannot be closed by software-only evidence.
