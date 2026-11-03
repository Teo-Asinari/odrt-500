"""Generate a functional schematic/netlist and preliminary harness register.

Semantic bundles deliberately do not pretend to specify pins, wire gauges,
isolation, safety integrity or a buildable circuit.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import textwrap

from odrt.config import ConfigError, load_yaml

DOMAINS = {'mains', 'pe', 'dc48', 'balance', 'logic', 'auxiliary', 'phase',
           'signal', 'brake', 'encoder', 'peer_external'}


def validate(definition):
    nodes, nets = definition['nodes'], definition['nets']
    ports = {f'{name}.{port}': domain for name, node in nodes.items()
             for port, domain in node['ports'].items()}
    if not ports or any(domain not in DOMAINS for domain in ports.values()):
        raise ConfigError('electrical definition: unknown or missing port domains')
    used = set()
    for name, endpoints in nets.items():
        if len(endpoints) < 2:
            raise ConfigError(f'{name}: net requires at least two endpoints')
        for endpoint in endpoints:
            if endpoint not in ports:
                raise ConfigError(f'{name}: unknown port {endpoint}')
            if endpoint in used:
                raise ConfigError(f'{name}: port used more than once: {endpoint}')
            used.add(endpoint)
        if len({ports[endpoint] for endpoint in endpoints}) != 1:
            raise ConfigError(f'{name}: incompatible electrical domains')
    if used != set(ports):
        raise ConfigError(f'electrical definition: unconnected ports {sorted(set(ports)-used)}')
    # These are narrow topology checks, not an isolation or functional safety proof.
    if set(nets['protective_earth']) != {
            'inlet.earth', 'input_protection.chassis', 'supply.frame',
            'enclosure.earth', 'peer_connector.shield'}:
        raise ConfigError('protective earth topology changed; bonding review required')
    if set(nets['motor_phases']) != {'phase_transfer.motor', 'motor.phases'}:
        raise ConfigError('motor connection bypasses proposed phase transfer')
    return ports


def generate(root=Path('.')):
    root = Path(root)
    source = root/'configs/electrical.yaml'
    definition = load_yaml(source)
    ports = validate(definition)
    digest = hashlib.sha256(source.read_bytes()+Path(__file__).read_bytes()).hexdigest()
    reports = root/'reports'
    (reports/'figures').mkdir(parents=True, exist_ok=True)
    # net diamonds preserve multi-drop nets; graph edges are connectivity, not cable routing.
    graph = ['digraph electrical {', 'rankdir=TB;', 'graph [bgcolor="white", ranksep=0.6];',
             'node [shape=box, style="rounded,filled", fillcolor="#edf2f5", fontname="sans-serif", fontsize=10];']
    for name, node in definition['nodes'].items():
        selection = node['selection'] if len(node['selection']) < 32 else 'unselected/custom'
        label = '\n'.join(textwrap.wrap(name.replace('_', ' '), 20))+'\n'+selection
        graph.append(f'{json.dumps(name)} [label={json.dumps(label)}];')
    colors = {'mains': '#a03a32', 'pe': '#498038', 'dc48': '#b97521', 'phase': '#6c5493'}
    for name, endpoints in definition['nets'].items():
        domain = ports[endpoints[0]]
        net_id = 'net_'+name
        color = colors.get(domain, '#567681')
        label = '\n'.join(textwrap.wrap(name.replace('_', ' '), 18))
        graph.append(f'{json.dumps(net_id)} [shape=diamond, label={json.dumps(label)}, fontsize=8, fillcolor="white"];')
        for index, endpoint in enumerate(endpoints):
            node, port = endpoint.split('.')
            start, end = (node, net_id) if index == 0 else (net_id, node)
            constraint = 'false' if domain == 'pe' or name == 'bus_return' else 'true'
            graph.append(f'{json.dumps(start)} -> {json.dumps(end)} '
                         f'[dir=none, constraint={constraint}, color="{color}", label={json.dumps(port)}, fontsize=7];')
    graph.append('}')
    build = root/'build/engineering'
    build.mkdir(parents=True, exist_ok=True)
    dot = build/'electrical.dot'
    dot.write_text('\n'.join(graph)+'\n')
    subprocess.run(['dot', '-Tsvg', str(dot), '-o', str(reports/'figures/electrical_functional.svg')], check=True)
    output = io.StringIO()
    fields = ['net', 'domain', 'semantic_endpoints', 'conductor_count', 'wire_gauge', 'length_mm',
              'connector_and_pinout', 'route', 'shield_and_separation', 'rating_evidence']
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for name, endpoints in definition['nets'].items():
        writer.writerow(dict(net=name, domain=ports[endpoints[0]], semantic_endpoints='; '.join(endpoints),
                             **{key: 'TBD' for key in fields[3:]}))
    (reports/'harness_preliminary.csv').write_text(output.getvalue())
    lines = ['# Preliminary electrical definition', '', f'Fingerprint: `{digest}`', '',
             '**Functional schematic, not a pin-level or fabrication schematic.** '
             'The candidate parts remain from the coupled reference; the compact buffer experiment is separate. '
             'Graph edges represent semantic connectivity and bundles, not conductor count or physical routes.', '',
             '[Open functional schematic](figures/electrical_functional.svg) · '
             '[Preliminary harness register](harness_preliminary.csv)', '',
             '| Function | Candidate / status | Definition |', '|---|---|---|']
    for name, node in definition['nodes'].items():
        lines.append(f'| {name} | {node["selection"]} | {node["description"]} |')
    lines += ['', '## Interfaces and unresolved engineering', '',
              'Mains and protective earth are explicit. DC return has no intentional chassis bond in this proposal; '
              'the final grounding, EMC and isolation plan must settle that choice. Semantic domain validation '
              'does not calculate creepage, clearance, dielectric strength or leakage.', '',
              'All supply, inverter, storage, dump, braking, logic and sensor functions need placement, '
              'protection ratings, connectors, wire sizing and thermal review. Every harness row retains TBD '
              'for unengineered details; bundles such as phases and cell taps must be expanded into conductors. '
              'Selected component labels refer to `data/engineering_components.yaml`, not verified pinouts.', '',
              'The phase transfer proposes break-before-make braking. It is not implemented or qualified. '
              'Its switching delay, contact failure, welded states and interlock must replace the current '
              'ideal fault response in simulation. The S1 inhibit input is not claimed to provide certified STO. '
              'The supervisor is an independent functional proposal; its power loss, common causes, diagnostics, '
              'latching and reset behavior remain unresolved.', '',
              'A local hardware stop path, bounded peer response, independent sensing plausibility, bank '
              'precharge and isolation, cell balance/voltage monitoring, thermal cutoffs, mount state and '
              'airflow feedback are explicitly included for subsequent circuit design and costing. '
              'Their presence in this graph does not establish effectiveness. The current simulator does '
              'not model these circuits or their component failures.', '',
              'Reproduce: `.venv/bin/python -m odrt.electrical_definition` (requires Graphviz `dot`).', '']
    (reports/'electrical_definition.md').write_text('\n'.join(lines))
    (reports/'electrical_netlist.json').write_text(json.dumps(
        {'fingerprint': digest, 'fidelity': 'functional semantic bundles; unqualified', **definition}, indent=2)+'\n')
    return definition


if __name__ == '__main__':
    generate()
