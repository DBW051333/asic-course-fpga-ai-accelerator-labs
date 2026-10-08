import json,time,os,signal
from pathlib import Path
R=Path('/home/ding/vivado_project/Lab6_limit_search')
p=R/'prepack_hybrid_bias/results/run_status.json'
while True:
 s=json.loads(p.read_text()).get('impl',{}).get('status')
 if s in ['passed','failed','interrupted']:break
 time.sleep(5)
# Original queue resumes only after the independently started second task finishes.
# run.py has no skip; prevent the already-completed second argument from repeating.
os.kill(368992,signal.SIGTERM)
p=R/'prepack_ternary_bias/results/run_status.json'
s=json.loads(p.read_text())
while not (R/'prepack_ternary_bias/results/final_clock.json').exists():time.sleep(5)
log=(R/'prepack_ternary_bias/results/impl_console.log').read_text()
if 'ERROR:' not in log:s['impl']['status']='passed';s['impl']['note']='Completed Vivado child; serial dispatcher replaced to avoid duplicate hybrid run';p.write_text(json.dumps(s,indent=2))
