#!/usr/bin/env python3
"""Serialize Vivado runs, keep complete logs and stage wall-clock times."""
import argparse,json,subprocess,time
from pathlib import Path
from search_quantization import ROOT

def main():
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['sim','synth','impl']);ap.add_argument('names',nargs='*');a=ap.parse_args()
    candidates=json.loads((ROOT/'results/candidates.json').read_text())
    names=a.names or [c['name'] for c in candidates]
    for name in names:
        d=ROOT/name;status=d/'results/run_status.json'
        state=json.loads(status.read_text()) if status.exists() else {}
        if state.get(a.stage,{}).get('status')=='passed':
            print('SKIP',a.stage,name,flush=True);continue
        state[a.stage]=dict(status='running',started=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
        status.write_text(json.dumps(state,indent=2));print('START',a.stage,name,flush=True)
        started=time.monotonic();log=d/f'results/{a.stage}_console.log'
        with log.open('w') as f:
            result=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source',str(d/f'tools/run_{a.stage}.tcl'),
                     '-log',str(d/f'results/{a.stage}_vivado.log'),'-journal',str(d/f'results/{a.stage}_vivado.jou')],cwd=d,stdout=f,stderr=subprocess.STDOUT)
        elapsed=round(time.monotonic()-started,2);s=log.read_text(errors='replace')
        passed=result.returncode==0 and 'ERROR:' not in s
        if a.stage=='sim':passed=passed and 'PASS: 48 overlapping' in s and 'errors=0' in s
        if a.stage=='synth':passed=passed and (d/'results/synth.dcp').exists()
        if a.stage=='impl':passed=passed and (d/'results/final_routed.dcp').exists()
        own_stage=state[a.stage]
        state=json.loads(status.read_text())
        state[a.stage]=own_stage
        state[a.stage].update(status='passed' if passed else 'failed',returncode=result.returncode,elapsed_seconds=elapsed)
        status.write_text(json.dumps(state,indent=2))
        print('END',a.stage,name,'passed' if passed else 'FAILED',elapsed,flush=True)
        if not passed:
            print(s[-5000:],flush=True);raise SystemExit(1)

if __name__=='__main__':main()
