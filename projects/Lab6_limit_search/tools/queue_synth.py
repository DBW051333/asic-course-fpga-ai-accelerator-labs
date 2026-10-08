from pathlib import Path
import json,time,sys
sys.path.insert(0,'/home/ding/vivado_project/Lab6_bottleneck_optimization/tools')
import run as runner
ROOT=Path('/home/ding/vivado_project/Lab6_limit_search');runner.ROOT=ROOT
after=sys.argv[1]
while True:
 p=ROOT/after/'results/run_status.json';state=json.loads(p.read_text()) if p.exists() else {}
 status=state.get('synth',{}).get('status')
 if status=='passed':break
 if status=='failed':raise SystemExit(f'Prerequisite {after} synthesis failed')
 time.sleep(5)
for name in sys.argv[2:]:
 if not runner.run(name,'synth'):raise SystemExit(1)
