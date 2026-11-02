"""Unit conversions. SI is used internally everywhere.

lbf (pound-force) and lb (pound-mass) are deliberately separate quantities:
1 lbf = 0.45359237 kg * 9.80665 m/s^2, exactly.
"""
from __future__ import annotations

LB_TO_KG = 0.45359237  # exact, international avoirdupois pound (mass)
STANDARD_GRAVITY_M_S2 = 9.80665  # exact, by definition
LBF_TO_N = LB_TO_KG * STANDARD_GRAVITY_M_S2  # 4.4482216152605 N, exact


def lbf_to_n(force_lbf):
    """Pound-force to newtons. Works on scalars and numpy arrays."""
    return force_lbf * LBF_TO_N


def n_to_lbf(force_n):
    """Newtons to pound-force. Works on scalars and numpy arrays."""
    return force_n / LBF_TO_N


def lb_to_kg(mass_lb):
    """Pound-mass to kilograms. Not a force conversion."""
    return mass_lb * LB_TO_KG


def cable_power_w(tension_n, velocity_m_s):
    """Mechanical power flowing from the cable into the device, in watts.

    Sign convention: velocity > 0 is cable extension (paying out from the drum).
    Positive power means the device absorbs energy (user does work on it);
    negative power means the device returns energy to the user/load.
    Tension is cable tension and is never negative (a cable cannot push).
    """
    return tension_n * velocity_m_s
