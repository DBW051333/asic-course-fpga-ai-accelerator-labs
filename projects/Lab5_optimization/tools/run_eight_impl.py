from pathlib import Path
import subprocess,time
r=Path('/home/ding/vivado_project/Lab5_optimization')
while not (r/'stream_pair256_dualtail_clk5/results/timing_impl.rpt').exists():time.sleep(5)
d=r/'stream_pair256_eighttail_clk5'
with (d/'results/impl_console.log').open('w') as out:
 c=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/run_impl.tcl','-log','results/impl.log','-journal','results/impl.jou'],cwd=d,stdout=out,stderr=subprocess.STDOUT)
print('eight implementation',c.returncode,flush=True)
