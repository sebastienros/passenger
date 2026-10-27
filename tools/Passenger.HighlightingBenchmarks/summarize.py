#!/usr/bin/env python3
import json, pathlib, statistics
root=pathlib.Path(__file__).resolve().parent
cases=json.loads((root/'cases.json').read_text())
rows=[]
for case in cases:
    engines={e:[json.loads(p.read_text()) for p in sorted((root/'results').glob(f'{case["file"]}-{e}-*.json'))] for e in ['textmatesharp','tint']}
    if any(len(ds)!=3 for ds in engines.values()): raise SystemExit('Expected three processes per engine: '+case['file'])
    hashes={d['colourHash'] for ds in engines.values() for d in ds}
    inputs={d['inputSha256'] for ds in engines.values() for d in ds}
    def median(e,phase,key):
        return statistics.median(statistics.median(s[key] for s in d['samples'] if s['phase']==phase) for d in engines[e])
    row={'case':case['file'],'lines':engines['tint'][0]['lines'],'identical':len(hashes)==1 and len(inputs)==1}
    for e in engines:
        row[e]={phase:{key:median(e,phase,key) for key in (['wallMs','cpuMs','allocatedBytes','workingSetBytes','peakWorkingSetBytes','workerMs'] if phase!='edit' else ['wallMs','cpuMs','allocatedBytes','workerMs','lines'])} for phase in ['cold','warm','edit']}
    rows.append(row)
(root/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
text=['| Workload (~10k lines) | Baseline ms | Tint ms | Speedup | CPU reduction | Allocation reduction | Baseline / Tint allocated MiB |', '|---|---:|---:|---:|---:|---:|---:|']
for r in rows:
    b,t=(r[e]['warm'] for e in ['textmatesharp','tint'])
    text.append(f'| {r["case"]} | {b["wallMs"]:.2f} | {t["wallMs"]:.2f} | {b["wallMs"]/t["wallMs"]:.2f}× | {(1-t["cpuMs"]/b["cpuMs"])*100:.1f}% | {(1-t["allocatedBytes"]/b["allocatedBytes"])*100:.1f}% | {b["allocatedBytes"]/2**20:.2f} / {t["allocatedBytes"]/2**20:.2f} |')
text+=['','| Workload | First use ms (base / Tint) | Working set MiB (base / Tint) | Edit µs (base / Tint) | Edit allocated bytes (base / Tint) | Lines per edit (base / Tint) |','|---|---:|---:|---:|---:|---:|']
for r in rows:
    b,t=(r[e] for e in ['textmatesharp','tint'])
    text.append(f'| {r["case"]} | {b["cold"]["wallMs"]:.1f} / {t["cold"]["wallMs"]:.1f} | {b["warm"]["workingSetBytes"]/2**20:.1f} / {t["warm"]["workingSetBytes"]/2**20:.1f} | {b["edit"]["wallMs"]*1000:.1f} / {t["edit"]["wallMs"]*1000:.1f} | {b["edit"]["allocatedBytes"]:.0f} / {t["edit"]["allocatedBytes"]:.0f} | {b["edit"]["lines"]:.1f} / {t["edit"]["lines"]:.1f} |')
(root/'tables.md').write_text('\n'.join(text)+'\n')
print('\n'.join(text))
print('All colour hashes identical:',all(r['identical'] for r in rows))
if not all(r['identical'] for r in rows):
    raise SystemExit('Input or colour hashes differ across engines')
