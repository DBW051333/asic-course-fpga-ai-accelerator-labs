import sys
from pathlib import Path
sys.path.insert(0,'/home/ding/vivado_project/Lab6_bottleneck_optimization/tools')
import run
run.ROOT=Path('/home/ding/vivado_project/Lab6_three_version_comparison')
# Original TB uses a different PASS summary, so do not apply optimized TB predicate.
import subprocess,json,time
D=run.ROOT/'original_int8'
with (D/'results/sim_console.log').open('w') as f:
 p=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source',str(D/'tools/run_sim.tcl')],cwd=D,stdout=f,stderr=subprocess.STDOUT)
s=(D/'results/sim_console.log').read_text();assert p.returncode==0 and 'mismatches=0' in s and 'ERROR:' not in s,s[-2000:]
print('\n'.join(x for x in s.splitlines() if x.startswith(('SUMMARY','PERFORMANCE'))),flush=True)
for stage in ['synth','impl']:
 if not run.run('original_int8',stage):raise SystemExit(1)
