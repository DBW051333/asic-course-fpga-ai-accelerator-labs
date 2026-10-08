from pathlib import Path
import subprocess
root=Path('/home/ding/vivado_project/Lab5_optimization')
for name in ('stream128_full','stream128_tree4','stream128_tree1222','stream64_tree1221'):
 d=root/name
 with (d/'results/sim_console.log').open('w') as f:
  result=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/create_sim.tcl','-log','results/sim.log','-journal','results/sim.jou'],cwd=d,stdout=f,stderr=subprocess.STDOUT)
 s=(d/'results/sim_console.log').read_text()
 lines=[x for x in s.splitlines() if 'MEASURE job=0' in x or x.startswith('PASS:') or x.startswith('FAIL') or x.startswith('ERROR:')]
 print(name,result.returncode,lines,flush=True)
 if result.returncode or 'PASS: three consecutive' not in s: break
