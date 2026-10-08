from pathlib import Path
import json,time,sys,subprocess
R=Path('/home/ding/vivado_project/Lab6_three_version_comparison');D=R/'original_int8'
while True:
 f=D/'results/run_status.json';s=json.loads(f.read_text()) if f.exists() else {}
 if any(v.get('status')=='failed' for v in s.values()):raise SystemExit('An earlier stage failed')
 if s.get('impl',{}).get('status')=='passed':break
 time.sleep(5)
sys.path.insert(0,'/home/ding/vivado_project/Lab6_bottleneck_optimization/tools');import run
run.ROOT=R
assert run.run('original_int8','final_verify')
log=(D/'results/final_verify_console.log').read_text();assert 'accuracy=37/42 mismatches=0' in log and 'INTERVAL cycles=' in log
subprocess.run([sys.executable,str(R/'collect_table.py')],check=True)
