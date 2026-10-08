#!/usr/bin/env python3
import json,subprocess,time,sys
from search_quantization import ROOT

def main():
    waiting=[sys.argv[1]] if len(sys.argv)>1 else ['q8_6_8_round_pack_d200','q8_lab6_d180','q8_8_8_round_pack_d200','q4_8_8_round_pack_d200']
    next_names=sys.argv[2:] if len(sys.argv)>1 else ['q8_product4_prereg_pack_d200','q8_product6_prereg_pack_d200']
    started=time.monotonic();print('Waiting for current synthesis queue',flush=True)
    while waiting:
        for name in waiting[:]:
            p=ROOT/name/'results/run_status.json'
            st=json.loads(p.read_text()).get('synth',{}).get('status') if p.exists() else None
            if st=='failed':raise RuntimeError('Earlier synthesis failed: '+name)
            if st=='passed':waiting.remove(name)
        if time.monotonic()-started>3600:raise TimeoutError(waiting)
        if waiting:time.sleep(5)
    raise SystemExit(subprocess.call(['python',str(ROOT/'tools/run_trials.py'),'synth',*next_names]))

if __name__=='__main__':main()
