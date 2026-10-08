from pathlib import Path
import sys,json,concurrent.futures
sys.path.insert(0,'/home/ding/vivado_project/Lab6_bottleneck_optimization/tools')
import run as runner
sys.path.insert(0,'/home/ding/vivado_project/Lab6_limit_search/tools')
from collect import resources
R=Path('/home/ding/vivado_project/Lab6_growth_trials');runner.ROOT=R
names=json.loads((R/'results/plan.json').read_text())['candidates']
def job(n):
 if not runner.run(n,'sim'):return
 if not runner.run(n,'synth'):return
 res=resources(R/n/'results/utilization_synth.rpt')
 limits={'dsp':220,'lut':53200,'ff':106400,'bram':140,'carry4':13300}
 if any(res.get(k,0)>v for k,v in limits.items()):
  (R/n/'results/budget_stop.json').write_text(json.dumps(res,indent=2));print('RESOURCE_STOP',n,res,flush=True);return
 print('BUDGET_OK',n,res,flush=True)
 runner.run(n,'impl')
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 list(pool.map(job,names))
