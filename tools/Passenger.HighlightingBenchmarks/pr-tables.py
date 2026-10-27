#!/usr/bin/env python3
"""Generate PR tables from validated total and instrumented summaries."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
total = {r['case']: r for r in json.loads((root / 'summary.json').read_text())}
diagnostics = {r['case']: r for r in json.loads((root / 'diagnostic-summary.json').read_text())}
names = {'xml.props': 'XML', 'css.css': 'CSS', 'javascript.js': 'JavaScript', 'less.less': 'Less',
         'json.json': 'JSON', 'yaml.yml': 'YAML', 'markdown.md': 'Markdown', 'html.html': 'HTML',
         'scss.scss': 'SCSS', 'shell.sh': 'Shell'}

def cell(b, t, unit, precision=2):
    return f'{b:,.{precision}f} → {t:,.{precision}f} {unit} (**{t / b:.2f}**)'

lines = ['## Full-file time', '',
         '| Workload | Total time: TMS → Tint (ratio) | Tokenizer time¹: TMS → Tint (ratio) |',
         '|---|---:|---:|']
for key in diagnostics:
    b, t = (total[key][e]['warm']['wallMs'] for e in ['textmatesharp', 'tint'])
    db, dt = (diagnostics[key][e]['pass']['TokenizerUs'] / 1000 for e in ['textmatesharp', 'tint'])
    lines.append(f'| {names[key]} | {cell(b, t, "ms")} | {cell(db, dt, "ms")} |')
lines += ['', '**Legend:** TMS = TextMateSharp. Ratio = Tint ÷ TMS; **0.33** means 33% of TMS’s time, or 67% less. Total time includes tokenization, line preparation, cache updates and background dispatch, excluding UI rendering. ¹Tokenizer time comes from separate instrumented runs, with measurement overhead. Columns are not additive and must not be subtracted to estimate overhead.', '',
          '## Allocations per edit', '',
          '| Workload | Total allocations/edit: TMS → Tint (ratio) | Tokenizer allocations/edit¹: TMS → Tint (ratio) |',
          '|---|---:|---:|']
for key in diagnostics:
    b, t = (total[key][e]['edit']['allocatedBytes'] for e in ['textmatesharp', 'tint'])
    db, dt = (diagnostics[key][e]['edits']['TokenizerAllocatedBytes'] for e in ['textmatesharp', 'tint'])
    lines.append(f'| {names[key]} | {cell(b, t, "B", 0)} | {cell(db, dt, "B", 0)} |')
lines += ['', '**Legend:** TMS = TextMateSharp. Ratio = Tint ÷ TMS. Total allocations cover the complete edit/highlighting operation, excluding UI rendering. ¹Tokenizer allocations come from separate instrumented runs. These are allocated managed bytes, not retained RAM. This table measures **one-character edits**, not full-file passes.', '',
          '## Full-file CPU, allocations and working set', '',
          '| Workload | Process CPU: TMS → Tint (ratio) | Allocated: TMS → Tint (ratio) | Working set: TMS → Tint (ratio) |',
          '|---|---:|---:|---:|']
for key, row in total.items():
    b, t = (row[e]['warm'] for e in ['textmatesharp', 'tint'])
    cells = [cell(b[k] / scale, t[k] / scale, unit) for k, scale, unit in
             [('cpuMs', 1, 'ms'), ('allocatedBytes', 2**20, 'MiB'), ('workingSetBytes', 2**20, 'MiB')]]
    lines.append(f'| {names[key]} | ' + ' | '.join(cells) + ' |')
lines += ['', '**Legend:** CPU is process CPU consumed during a full pass, summed across threads. Allocated is managed allocation during that pass. Working set is sampled after forced GC and includes runtime, JIT, heaps and native libraries; it is not the highlighter’s retained memory. All ratios are Tint ÷ TMS. These measurements exclude IDE rendering and language-server activity.', '']
(root / 'pr-tables.md').write_text('\n'.join(lines))
print('\n'.join(lines))
