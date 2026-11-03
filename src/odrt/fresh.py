"""Exit 0 when a study's committed report already matches its current inputs.

Used by the Makefile to skip expensive regeneration: every slow study records
the SHA-256 fingerprint of its configuration, data and model source when it
publishes. If the fingerprint recomputed now is identical, rerunning would only
reproduce the same report. Set FORCE=1 to rerun anyway.

    python -m odrt.fresh coupled-verify && echo current || echo stale
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

# study -> (report, report key, module, fingerprint function, extra report check)
STUDIES = {
    'coupled': ('reports/coupled.json', 'input_hash', 'odrt.coupled', 'fingerprint', None),
    'coupled-verify': ('reports/coupled.json', 'input_hash', 'odrt.coupled', 'fingerprint',
                       lambda r: r.get('verification') is not None),
    'buffer-study': ('reports/compact_buffer.json', 'fingerprint', 'odrt.buffer_study', 'study_fingerprint', None),
    'compact-candidate': ('reports/compact_candidate.json', 'fingerprint', 'odrt.compact_candidate',
                          'candidate_fingerprint', None),
    'revision-power': ('reports/revision_power.json', 'fingerprint', 'odrt.revision_power',
                       'revision_fingerprint', None),
    'r2-candidate': ('reports/r2_candidate.json', 'fingerprint', 'odrt.r2_candidate', 'r2_fingerprint', None),
    'control-study': ('reports/control_study.json', 'fingerprint', 'odrt.control_study', 'study_fingerprint', None),
    'r3c-candidate': ('reports/r3c_candidate.json', 'fingerprint', 'odrt.r2_candidate', 'r3c_fingerprint', None),
    'r3-candidate': ('reports/r3_candidate.json', 'fingerprint', 'odrt.r2_candidate', 'r3_fingerprint', None),
    'r4-candidate': ('reports/r4_candidate.json', 'fingerprint', 'odrt.r2_candidate', 'r4_fingerprint', None),
    'fast-study': ('reports/fast_motion_study.json', 'fingerprint', 'odrt.fast_motion_study', 'study_fingerprint', None),
}


def is_fresh(study: str, root: Path = Path('.')) -> bool:
    report, key, module, function, extra = STUDIES[study]
    path = Path(root) / report
    if not path.exists():
        return False
    stored = json.loads(path.read_text())
    current = getattr(importlib.import_module(module), function)(Path(root))
    return stored.get(key) == current and (extra is None or extra(stored))


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] not in STUDIES:
        print(f'usage: python -m odrt.fresh {{{",".join(STUDIES)}}}', file=sys.stderr)
        return 2
    if os.environ.get('FORCE'):
        return 1
    fresh = is_fresh(argv[0])
    print(f'{argv[0]}: {"report current, skipping" if fresh else "inputs changed, regenerating"}', flush=True)
    return 0 if fresh else 1


if __name__ == '__main__':
    raise SystemExit(main())
