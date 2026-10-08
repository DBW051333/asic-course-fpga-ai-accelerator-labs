from pathlib import Path
import subprocess,time
r=Path('/home/ding/vivado_project/Lab5_optimization')
while not (r/'stream_pair256_quadtail_clk5/results/timing_impl.rpt').exists():time.sleep(5)
d=r/'stream_pair256_quad_tree7_clk4p8'
while not (d/'results/sim_console.log').exists() or 'PASS: three consecutive' not in (d/'results/sim_console.log').read_text():time.sleep(5)
with (d/'results/impl_console.log').open('w') as out:
 c=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/run_impl.tcl','-log','results/impl.log','-journal','results/impl.jou'],cwd=d,stdout=out,stderr=subprocess.STDOUT)
print('deep implementation',c.returncode,flush=True)
