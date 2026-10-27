#!/usr/bin/env python3
"""Expose the spread hidden by the median of process medians."""
import json
import statistics
from pathlib import Path

root = Path(__file__).resolve().parent
lines = ['# Full-pass timing variability', '',
         'Each cell lists the three process medians in execution-round order, in milliseconds. These are observed ranges, not confidence intervals. Tiered compilation was left enabled; seven measured passes do not guarantee steady state.', '',
         '| Workload | TextMateSharp process medians (ms) | Tint process medians (ms) |',
         '|---|---:|---:|']
for case in json.loads((root / 'cases.json').read_text()):
    cells = []
    for engine in ['textmatesharp', 'tint']:
        paths = sorted((root / 'results').glob(f'{case["file"]}-{engine}-*.json'))
        assert len(paths) == 3
        values = [statistics.median(s['wallMs'] for s in json.loads(p.read_text())['samples'] if s['phase'] == 'warm') for p in paths]
        cells.append(', '.join(f'{v:,.2f}' for v in values))
    lines.append(f'| {case["file"]} | ' + ' | '.join(cells) + ' |')
(root / 'variability.md').write_text('\n'.join(lines) + '\n')
