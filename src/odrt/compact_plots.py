"""Plot saved, fingerprint-checked candidate traces without rerunning physics."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from odrt.compact_candidate import candidate_fingerprint
from odrt.config import ConfigError


def generate(root=Path('.')):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root=Path(root);report=json.loads((root/'reports/compact_candidate.json').read_text())
    if report['fingerprint']!=candidate_fingerprint(root):
        raise ConfigError('candidate traces/report are stale; regenerate before plotting')
    provenance={'candidate_fingerprint':report['fingerprint'],
                'plot_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'traces':{}}
    def trace(bank,case):
        record=report['variants'][bank]['cases'][case]
        if 'solver_failure' in record:raise ConfigError('cannot plot failed candidate integration')
        path=root/record['trace']
        provenance['traces'][record['trace']]=hashlib.sha256(path.read_bytes()).hexdigest()
        with np.load(path) as archive:return {k:archive[k] for k in archive.files}
    figures=root/'reports/figures';figures.mkdir(parents=True,exist_ok=True)
    colors={'compact_nominal':'#307f83','compact_aged':'#b15c47'}
    fig,axes=plt.subplots(3,1,figsize=(11,8),sharex=True)
    for bank in colors:
        data=trace(bank,'paired_heavy_full');t=data['t'];label='Fresh bank' if bank=='compact_nominal' else 'Aged corner'
        axes[0].plot(t,data['unit_0.tension_n'],color=colors[bank],label=label)
        axes[1].plot(t,data['unit_0.bus_v'],color=colors[bank],label=label)
        axes[2].plot(t,data['unit_0.drive_enabled'],color=colors[bank],label=label)
    axes[0].plot(t,data['unit_0.command_n'],color='#333333',ls='--',lw=1,label='Requested')
    axes[1].axhline(40,color='#777777',ls=':',lw=1,label='Proposed UV trip')
    for ax,label in zip(axes,('Unit 0 tension N','Unit 0 bus V','Drive enabled')):
        ax.set_ylabel(label);ax.grid(alpha=.2);ax.legend(loc='upper right',fontsize=8)
    axes[-1].set_xlabel('Time s');axes[-1].set_ylim(-.1,1.1)
    fig.suptitle('Compact candidate: paired heavy set, fresh versus aged bank')
    fig.text(.5,.015,'Conditional model — aged-cell shutdown is a failed operating case, not improved thermal performance.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,.95));fig.savefig(figures/'compact_candidate_tracking.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(11,9),sharex=True)
    for case,color,label in (('left_power_loss_buffered','#b15c47','Buffered loss / independent'),
                             ('left_power_loss_buffered_coordinated','#307f83','Buffered loss / peer stop')):
        data=trace('compact_nominal',case)
        axes[0].plot(data['t'],np.rad2deg(data['bar_angle_rad']),color=color,label=label)
    for bank,color in colors.items():
        data=trace(bank,'paired_release_asymmetric')
        axes[1].plot(data['t'],np.rad2deg(data['bar_angle_rad']),color=color,
                     label='Fresh bank' if bank=='compact_nominal' else 'Aged corner')
    for unit,color in ((0,'#4a6990'),(1,'#ab7c39')):
        axes[2].plot(data['t'],data[f'unit_{unit}.tension_n'],color=color,label=f'Unit {unit}, aged release')
    for ax,label in zip(axes,('Bar angle °','Release bar angle °','Cable tension N')):
        ax.set_ylabel(label);ax.grid(alpha=.2);ax.legend(loc='upper left',fontsize=8)
    axes[-1].set_xlabel('Time s')
    fig.suptitle('Compact candidate fault policies and 1% release imbalance')
    fig.text(.5,.015,'Parallel-cable rigid-bar model; large rotations and release behavior require physical model validation.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,.95));fig.savefig(figures/'compact_candidate_faults.png',dpi=160);plt.close(fig)
    (root/'reports/compact_plot_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    return provenance


if __name__=='__main__':
    generate()
