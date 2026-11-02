"""Swivel cable exit: loads over an angled-pull envelope and deck grip (first pass, A-025)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from odrt.config import ConfigError, check_keys, load_yaml, number
from odrt.units import lbf_to_n

G = 9.80665


@dataclass(frozen=True)
class SwivelCfg:
    sheave_r_mm: float
    head_h_mm: float
    max_tilt_deg: float
    bearing_pcd_mm: float
    dome_r_mm: float
    envelope: tuple          # ((tilt deg, tension lbf), ...)
    snap_factor: float
    min_user_kg: float
    deck_mu: float


def load_swivel(path: Path) -> SwivelCfg:
    d = load_yaml(path)
    w = str(path)
    check_keys(d, w, ["exit_sheave_radius_mm", "head_height_mm", "max_tilt_deg", "bearing_pcd_mm", "dome_radius_mm",
                      "envelope", "snap_factor", "min_user_mass_kg", "deck_friction"])
    env = d["envelope"]
    if not isinstance(env, list) or len(env) < 2:
        raise ConfigError(f"{w}.envelope: need at least two [tilt, tension] points")
    pts = tuple((number(a, f"{w}.envelope", minimum=0, maximum=90), number(t, f"{w}.envelope", minimum=0))
                for a, t in env)
    if [a for a, _ in pts] != sorted(a for a, _ in pts):
        raise ConfigError(f"{w}.envelope: tilts must increase")
    pos = dict(minimum=0, exclusive_minimum=True)
    return SwivelCfg(number(d["exit_sheave_radius_mm"], f"{w}.exit_sheave_radius_mm", **pos),
                     number(d["head_height_mm"], f"{w}.head_height_mm", **pos),
                     number(d["max_tilt_deg"], f"{w}.max_tilt_deg", minimum=0, maximum=90),
                     number(d["bearing_pcd_mm"], f"{w}.bearing_pcd_mm", **pos),
                     number(d["dome_radius_mm"], f"{w}.dome_radius_mm", **pos), pts,
                     number(d["snap_factor"], f"{w}.snap_factor", minimum=1),
                     number(d["min_user_mass_kg"], f"{w}.min_user_mass_kg", **pos),
                     number(d["deck_friction"], f"{w}.deck_friction", **pos))


def case(cfg: SwivelCfg, tilt_deg: float, tension_lbf: float) -> dict:
    """Loads for one envelope point (tension T in both rope legs at the exit sheave)."""
    t = lbf_to_n(tension_lbf)
    th = math.radians(tilt_deg)
    ts = t * cfg.snap_factor
    # exit sheave: rope arrives vertically from below and leaves at tilt th -> wrap th
    axle = 2 * ts * math.sin(th / 2) if tilt_deg > 0 else 0.0
    # swivel bearing: net force from the two legs = T (down, incoming) + T (outgoing, up at th) acts on the head
    fx = ts * math.sin(th)              # horizontal, toward the user
    fz_up = ts * math.cos(th) - ts      # outgoing pulls up, incoming pulls down -> net (<= 0 is down)
    moment = fx * cfg.head_h_mm / 1000  # overturning moment on the swivel bearing
    # deck grip: the user's feet react the horizontal pull; normal force = weight + vertical rope component
    w = cfg.min_user_kg * G
    mu_needed = (t * math.sin(th)) / max(w + t * math.cos(th), 1e-9)
    return {"tilt_deg": tilt_deg, "tension_lbf": tension_lbf, "exit_axle_n": axle, "bearing_radial_n": fx,
            "bearing_axial_n": fz_up, "bearing_moment_nm": moment, "mu_needed": mu_needed,
            "grip_ok": mu_needed <= cfg.deck_mu}


def envelope(cfg: SwivelCfg) -> list:
    return [case(cfg, a, t) for a, t in cfg.envelope]


def max_safe_tension_lbf(cfg: SwivelCfg, tilt_deg: float) -> float:
    """Largest tension a min-mass user can pull at this tilt before the feet slip (mu = deck_mu)."""
    th = math.radians(tilt_deg)
    w = cfg.min_user_kg * G
    denom = math.sin(th) - cfg.deck_mu * math.cos(th)
    if denom <= 0:
        return math.inf
    return cfg.deck_mu * w / denom / 4.4482216152605
