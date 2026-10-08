from pathlib import Path
import subprocess,json,time,sys
ROOT=Path('/home/ding/vivado_project/Lab6_bottleneck_optimization')
def run(name,stage):
    d=ROOT/name;r=d/'results';status=r/'run_status.json'
    state=json.loads(status.read_text()) if status.exists() else {}
    state[stage]=dict(status='running',started=time.strftime('%Y-%m-%dT%H:%M:%S%z'));status.write_text(json.dumps(state,indent=2))
    print('START',name,stage,flush=True);t=time.monotonic()
    with (r/f'{stage}_console.log').open('w') as f:
        p=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source',str(d/f'tools/run_{stage}.tcl'),'-log',str(r/f'{stage}_vivado.log'),'-journal',str(r/f'{stage}_vivado.jou')],cwd=d,stdout=f,stderr=subprocess.STDOUT)
    s=(r/f'{stage}_console.log').read_text(errors='replace');ok=p.returncode==0 and 'ERROR:' not in s
    if stage=='sim':ok=ok and 'PASS: 48 overlapping' in s and 'errors=0' in s
    if stage=='impl':ok=ok and (r/'final_routed.dcp').exists()
    if stage=='synth':ok=ok and (r/'synth.dcp').exists()
    state=json.loads(status.read_text());state[stage].update(status='passed' if ok else 'failed',elapsed_seconds=round(time.monotonic()-t,2),returncode=p.returncode);status.write_text(json.dumps(state,indent=2))
    print('END',name,stage,state[stage],flush=True)
    if not ok:print(s[-3500:],flush=True);return False
    return True
if __name__=='__main__':
    for arg in sys.argv[1:]:
        name,stage=arg.split(':')
        if not run(name,stage):raise SystemExit(1)
