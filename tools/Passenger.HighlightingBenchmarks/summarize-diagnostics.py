#!/usr/bin/env python3
import json,pathlib,statistics
root=pathlib.Path(__file__).resolve().parent
out=root/'diagnostic-results'
rows=[]
for case in ['xml.props','css.css','javascript.js','less.less']:
    engines={}
    hashes=set()
    for engine in ['textmatesharp','tint']:
        d=json.loads((out/f'{case}-{engine}-0.json').read_text())
        hashes.add((d['inputSha256'],d['colourHash']))
        g=d['diagnostics']['Groups'];frequency=d['diagnostics']['Frequency']
        def median(phase,event,key):
            ids=range(3,10) if phase=='pass' else range(1,6)
            return statistics.median(g[f'{phase}-{i}/{event}']['Totals'][key]/g[f'{phase}-{i}/Pass']['Count'] for i in ids)
        engines[engine]={}
        for phase in ['pass','edits']:
            engines[engine][phase]={key:median(phase,'Pass',key) for key in ['WorkerAllocatedBytes','TokenizerAllocatedBytes','LinePreparationAllocatedBytes','OtherWorkerAllocatedBytes','ReadLines','SkippedLines','StoppedLines','UnknownStopStatusLines']}
            for key in ['WorkerTicks','TokenizerTicks','LinePreparationTicks','OtherWorkerTicks','LockWaitTicks','WorkerQueueTicks']:
                engines[engine][phase][key.replace('Ticks','Us')]=median(phase,'Pass',key)*1e6/frequency
            for key in ['QueueTicks','CallbackTicks','CallbackAllocatedBytes']:
                engines[engine][phase]['Publication'+key.replace('Ticks','Us')]=median(phase,'Publication',key)*(1e6/frequency if key.endswith('Ticks') else 1)
    if len(hashes)!=1: raise SystemExit('Input or colour mismatch: '+case)
    rows.append({'case':case,**engines})
(root/'diagnostic-summary.json').write_text(json.dumps(rows,indent=2)+'\n')
text=['| Workload | Full-pass tokenizer ms (base / Tint) | Edit tokenizer µs (base / Tint) | Edit tokenizer bytes (base / Tint) | Edit preparation/mapping bytes (base / Tint) | Edit other-worker bytes (base / Tint) |', '|---|---:|---:|---:|---:|---:|']
for row in rows:
    b,t=(row[e] for e in ['textmatesharp','tint'])
    text.append(f'| {row["case"]} | {b["pass"]["TokenizerUs"]/1000:.2f} / {t["pass"]["TokenizerUs"]/1000:.2f} | {b["edits"]["TokenizerUs"]:.2f} / {t["edits"]["TokenizerUs"]:.2f} | {b["edits"]["TokenizerAllocatedBytes"]:.0f} / {t["edits"]["TokenizerAllocatedBytes"]:.0f} | {b["edits"]["LinePreparationAllocatedBytes"]:.0f} / {t["edits"]["LinePreparationAllocatedBytes"]:.0f} | {b["edits"]["OtherWorkerAllocatedBytes"]:.0f} / {t["edits"]["OtherWorkerAllocatedBytes"]:.0f} |')
(root/'diagnostic-tables.md').write_text('\n'.join(text)+'\n')
print('\n'.join(text))
