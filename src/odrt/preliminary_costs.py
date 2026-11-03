"""Full-function preliminary cost allowances; never mislabel these as quotes."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from odrt.config import ConfigError, load_yaml
from odrt.electrical_definition import validate

VOLUMES = ('prototype', '100', '1000')


def cost_band(parts, hours, production):
    """Bounding corners, not probabilistic confidence intervals."""
    low = (parts[0]+hours[0]*production['labor_usd_per_hour'][0]) / production['yield_fraction'][1]
    high = (parts[1]+hours[1]*production['labor_usd_per_hour'][1]) / production['yield_fraction'][0]
    low *= (1+production['factory_overhead_fraction'][0])*(1+production['warranty_fraction'][0])
    high *= (1+production['factory_overhead_fraction'][1])*(1+production['warranty_fraction'][1])
    return [low, high]


def retail_band(cost, production):
    return [cost[0]/(1-production['distribution_fraction_of_retail'][0]-production['gross_margin_fraction_of_retail'][0]),
            cost[1]/(1-production['distribution_fraction_of_retail'][1]-production['gross_margin_fraction_of_retail'][1])]


def generate(root=Path('.')):
    root = Path(root)
    source, electrical_source = root/'data/preliminary_costs.yaml', root/'configs/electrical.yaml'
    data, electrical = load_yaml(source), load_yaml(electrical_source)
    validate(electrical)
    seen, covered = set(), []
    for row in data['items']:
        if row['id'] in seen or set(row) != {'id', 'scope', 'covers', 'description', 'ranges'}:
            raise ConfigError('cost item requires unique ID and exact fields')
        seen.add(row['id'])
        covered.extend(row['covers'])
        if len(row['ranges']) != 3 or any(len(b) != 2 or not 0 < b[0] <= b[1] for b in row['ranges']):
            raise ConfigError(f'{row["id"]}: invalid cost ranges')
    if len(covered) != len(set(covered)) or set(covered) != set(electrical['nodes']):
        raise ConfigError('electrical functions require exactly one cost allocation each')
    digest = hashlib.sha256(source.read_bytes()+electrical_source.read_bytes()+Path(__file__).read_bytes()).hexdigest()
    p = data['production']
    totals = {}
    for index, volume in enumerate(VOLUMES):
        scopes = {scope: [sum(row['ranges'][index][side] for row in data['items'] if row['scope'] == scope)
                          for side in (0, 1)] for scope in ('unit', 'board', 'wall', 'rack', 'door')}
        unit = cost_band(scopes['unit'], p['assembly_calibration_test_hours'][index], p)
        # Accessory labor is charged once per accessory; two wall/rack/door adapters
        # in the paired totals are charged twice. Per-unit interface is already in unit.
        accessories = {name: cost_band(scopes[name], p['accessory_assembly_hours'][index], p)
                       for name in ('board', 'wall', 'rack', 'door')}
        systems = {'one_unit': unit, 'two_units': [2*x for x in unit]}
        for name, accessory in accessories.items():
            count = 1 if name == 'board' else 2
            systems['pair_with_'+name] = [2*unit[s]+count*accessory[s] for s in (0, 1)]
        quantity = 1 if volume == 'prototype' else int(volume)
        nre_per_unit = [value/quantity for value in p['nre_usd']]
        totals[volume] = {'parts_by_scope_usd': scopes, 'unit_factory_cost_usd': unit,
                          'accessory_factory_cost_usd': accessories, 'systems_factory_cost_usd': systems,
                          'unit_retail_before_nre_usd': retail_band(unit, p),
                          'pair_board_retail_before_nre_usd': retail_band(systems['pair_with_board'], p),
                          'nre_per_unit_if_amortized_usd': nre_per_unit,
                          'unit_retail_with_nre_usd': retail_band([unit[s]+nre_per_unit[s] for s in (0, 1)], p)}
    result = {'fingerprint': digest, 'basis': data['basis'], 'supplier_quotes_in_total': 0,
              'electrical_functions_allocated': len(covered), 'cost_lines': len(data['items']),
              'currency': data['currency'], 'totals': totals, 'production_assumptions': p,
              'exclusions': data['exclusions'], 'assessment': 'planning allowance; commercial target unproven'}
    (root/'reports/preliminary_costs.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    band = lambda values: f'${math.floor(values[0]):,}–${math.ceil(values[1]):,}'
    lines = ['# Complete-function preliminary cost allowances', '', f'Fingerprint: `{digest}`', '',
             '**Planning estimates, not supplier quotes.** '+data['basis'], '',
             'These allowances include every function in the preliminary electrical definition, plus mechanics, '
             'cable routing, arrestor, harness, retention, assembly, calibration, test, board and adapters. '
             'They supersede the historical priced-floor interpretation for planning, but are not a validated BOM '
             'for a compact machine. No volume quotation has been obtained. All costs are USD.', '',
             '| Line / scope | Prototype parts | 100-unit parts | 1000-unit parts |', '|---|---:|---:|---:|']
    for row in data['items']:
        lines.append(f'| {row["description"]} / {row["scope"]} | '+ ' | '.join(band(v) for v in row['ranges'])+' |')
    lines += ['', '## System totals', '', '| Procurement volume (units) | One unit factory | Two units + board factory | '
              'Unit retail before NRE | Pair + board retail before NRE |', '|---|---:|---:|---:|---:|']
    for volume, t in totals.items():
        lines.append(f'| {volume} | {band(t["unit_factory_cost_usd"])} | '
                     f'{band(t["systems_factory_cost_usd"]["pair_with_board"])} | '
                     f'{band(t["unit_retail_before_nre_usd"])} | {band(t["pair_board_retail_before_nre_usd"])} |')
    lines += ['', 'A paired system has two units and one board, or two separate mounting adapters. '
              'Adapter alternatives are not all charged together. The JSON includes bare pairs and wall/rack/door pairs. '
              'The door allowance does not establish door compatibility or load capability.', '',
              'Factory cost = (parts + assembly/calibration/test labor) / yield × (1 + factory overhead) '
              '× (1 + warranty allowance). Retail = factory cost / (1 − distribution share − gross-margin share). '
              'Assembly labor is '+str(p['assembly_calibration_test_hours'])+' hours by volume; labor rate '
              +band(p['labor_usd_per_hour'])+'/hour. Yield is 90–98%, factory overhead 10–30%, warranty 3–10%, '
              'distribution 15–35% of retail and gross margin 30–50% of retail. '
              'Bounds combine favorable or adverse assumptions; they are not statistical confidence limits.', '',
              '## Development and uncertainty', '',
              f'NRE allowance: {band(p["nre_usd"])}. '+p['nre_basis']+' '
              'Procurement volumes count modules, not pairs; NRE amortization therefore divides by modules. '
              'Prototype amortization assigns the whole development allowance to one unit and is not its marginal build cost.', '',
              '| Volume | NRE per unit | Unit retail with NRE amortization |', '|---|---:|---:|']
    for volume, t in totals.items():
        lines.append(f'| {volume} | {band(t["nre_per_unit_if_amortized_usd"])} | {band(t["unit_retail_with_nre_usd"])} |')
    lines += ['', 'Listing context only: [CubeMars RO100 listing]('+data['listing_context']['source']+
              ') showed $156.90 and sold-out text on 2026-11-02; exact variant and stock remain unconfirmed. '
              'No quote from that page is counted in these totals.', '',
              'Excluded: '+data['exclusions'], '',
              '**Assessment: REVISE.** A $500 retail unit is unsupported. Replacing the planning ranges with '
              'part-specific quotes, production drawings, supplier process feedback and measured assembly/test '
              'time is required before a commercial feasibility decision. Geometry, fault-response circuitry '
              'and thermal redesign can move these ranges materially.', '',
              'Reproduce: `.venv/bin/python -m odrt.preliminary_costs`.', '']
    (root/'reports/preliminary_costs.md').write_text('\n'.join(lines))
    return result


if __name__ == '__main__':
    generate()
