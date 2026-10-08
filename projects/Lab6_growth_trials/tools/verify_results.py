from pathlib import Path
import sys,json,time,subprocess
R=Path('/home/ding/vivado_project/Lab6_growth_trials')
sys.path.insert(0,'/home/ding/vivado_project/Lab6_bottleneck_optimization/tools')
import run as runner
runner.ROOT=R
names=json.loads((R/'results/plan.json').read_text())['candidates']
while True:
 states=[json.loads((R/n/'results/run_status.json').read_text()) for n in names]
 if all(x.get('impl',{}).get('status') in ('passed','failed') for x in states):break
 time.sleep(5)
for n in names:
 if (R/n/'results/final_routed.dcp').exists():
  if not runner.run(n,'final_verify'):raise SystemExit(1)
  s=(R/n/'results/final_verify_console.log').read_text()
  if 'PASS: 48 overlapping' not in s or 'errors=0' not in s:raise SystemExit('Value validation failed: '+n)
subprocess.run([sys.executable,str(R/'tools/collect_results.py')],check=True)
subprocess.run([sys.executable,str(R/'tools/write_report.py')],check=True)
