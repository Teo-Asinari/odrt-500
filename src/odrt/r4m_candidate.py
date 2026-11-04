"""R4 with the motor-study variant R4M_VARIANT, run through the R4 full suite (make r4m-candidate).

Study, not the R4 candidate. Registered into odrt.r2_candidate.STUDIES here rather than in that module,
so adding it does not change the fingerprint of every study built on r2_candidate.py.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from odrt import r2_candidate
from odrt.config import load_yaml

R4M_VARIANT = 'tbm_6'


def load_r4m(root=Path('.')):
    """R4 with the TBM2G-11526D at 6:1 (configs/motor_study.yaml variant R4M_VARIANT)."""
    from odrt.motor_study import apply_variant, load_candidates
    cfg, parts, variants, derived, source, support = r2_candidate.load_r4(root)
    changes = load_yaml(Path(root)/'configs/motor_study.yaml')['variants'][R4M_VARIANT]
    cfg, parts = apply_variant(cfg, parts, load_candidates(root), changes)
    return cfg, parts, variants, dict(derived, motor_variant={'name': R4M_VARIANT, 'changes': changes}), source, support


def r4m_fingerprint(root=Path('.')):
    from odrt.motor_study import study_fingerprint
    h = hashlib.sha256((study_fingerprint(root)+R4M_VARIANT).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


r2_candidate.STUDIES['r4m'] = dict(load=load_r4m, fingerprint=r4m_fingerprint,
                                   title='R4 with the Kollmorgen TBM2G-11526D at 6:1 (motor study variant tbm_6; study, not adopted)',
                                   extra=())
r2_candidate.CONTROL_EXTRA['r4m'] = r2_candidate.CONTROL_EXTRA['r4']


if __name__ == '__main__':
    result = r2_candidate.run(study='r4m')
    if not result['verification']['pass'] or any(not m.get('numerical_valid', False)
                                                 for b in result['banks'].values() for m in b.values()):
        raise SystemExit('R4M numerical verification incomplete; failures retained')
