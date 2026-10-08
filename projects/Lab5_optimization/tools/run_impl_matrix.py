from pathlib import Path
import subprocess
r=Path('/home/ding/vivado_project/Lab5_optimization')
for name in ('stream128_exact','stream128_tree4','stream128_tree1222','stream128_full','stream64_tree1221'):
 d=r/name
 with (d/'results/impl_console.log').open('w') as f:
  p=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/run_impl.tcl','-log','results/impl.log','-journal','results/impl.jou'],cwd=d,stdout=f,stderr=subprocess.STDOUT)
 print(name,'implementation exit',p.returncode,flush=True)
 if p.returncode: print('\n'.join((d/'results/impl_console.log').read_text().splitlines()[-12:]),flush=True)
