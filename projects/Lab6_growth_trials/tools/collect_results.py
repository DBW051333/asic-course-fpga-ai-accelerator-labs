from pathlib import Path
import sys,json,csv
sys.path.insert(0,'/home/ding/vivado_project/Lab6_limit_search/tools')
from collect import row
R=Path('/home/ding/vivado_project/Lab6_growth_trials');plan=json.loads((R/'results/plan.json').read_text())
rows=[row(Path(plan['baseline']))]+[row(R/n) for n in plan['candidates']]
for x in rows:
 if 'latency_ns' in x:x['improvement_percent']=round(100*(1-x['latency_ns']/plan['baseline_ns']),3)
 p=R/x['name']/'results/budget_stop.json'
 if p.exists():x['resource_stop']=json.loads(p.read_text())
(R/'results/comparison.json').write_text(json.dumps(rows,indent=2))
keys=list(dict.fromkeys(k for r in rows for k in r))
with (R/'results/comparison.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
for x in rows:print(json.dumps(x))
