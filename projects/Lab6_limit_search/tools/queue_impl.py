from pathlib import Path
import sys,json,time
sys.path.insert(0,'/home/ding/vivado_project/Lab6_bottleneck_optimization/tools')
import run as runner
ROOT=Path('/home/ding/vivado_project/Lab6_limit_search');runner.ROOT=ROOT
# One implementation worker; a separate synthesis worker can run when memory permits.
for name in sys.argv[1:]:
 d=ROOT/name
 while True:
  p=d/'results/run_status.json';s=json.loads(p.read_text()) if p.exists() else {}
  if s.get('impl',{}).get('status')=='passed':print('SKIP completed',name,flush=True);break
  if s.get('impl',{}).get('status')=='running':time.sleep(5);continue
  cfg=json.loads((d/'config.json').read_text())
  if not cfg.get('physical_only') and s.get('synth',{}).get('status')!='passed':
   if s.get('synth',{}).get('status')=='failed':print('SKIP synthesis failure',name,flush=True);break
   time.sleep(5);continue
  runner.run(name,'impl');break
