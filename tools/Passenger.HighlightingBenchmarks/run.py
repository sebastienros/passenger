#!/usr/bin/env python3
"""Run Release baseline and candidate in fresh, alternating processes. No concurrent workloads."""
import argparse, json, pathlib, subprocess, time
p=argparse.ArgumentParser()
p.add_argument('--dotnet',default='dotnet')
p.add_argument('--baseline',required=True)
p.add_argument('--candidate',required=True)
p.add_argument('--rounds',type=int,default=3)
a=p.parse_args()
root=pathlib.Path(__file__).resolve().parent
out=root/'results';out.mkdir(exist_ok=True)
cases=json.loads((root/'cases.json').read_text())
failed=[]
for round in range(a.rounds):
    for case in cases:
        engines=[('textmatesharp',a.baseline),('tint',a.candidate)]
        if round%2: engines.reverse()
        for engine,dll in engines:
            target=out/f'{case["file"]}-{engine}-{round}.json'
            start=time.monotonic()
            result=subprocess.run([a.dotnet,dll,str(root/'fixtures'/case['file']),str(case['repeat']),str(target)],capture_output=True,text=True,timeout=240)
            print(f'{case["file"]} {engine} round={round} exit={result.returncode} seconds={time.monotonic()-start:.2f}',flush=True)
            if result.returncode:
                (target.with_suffix('.error.txt')).write_text(result.stdout+result.stderr)
                failed.append(str(target))
if failed: raise SystemExit('Failed: '+', '.join(failed))
