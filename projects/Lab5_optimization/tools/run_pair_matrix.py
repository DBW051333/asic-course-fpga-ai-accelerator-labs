from pathlib import Path
import subprocess
r=Path('/home/ding/vivado_project/Lab5_optimization')
for name in ('stream_pair128_staged','stream_pair171_staged','stream_pair256_staged','stream_pair171','stream_pair256_hybrid'):
 d=r/name
 if 'staged' in name:
  with (d/'results/sim_console.log').open('w') as f:
   p=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/create_sim.tcl','-log','results/sim.log','-journal','results/sim.jou'],cwd=d,stdout=f,stderr=subprocess.STDOUT)
  s=(d/'results/sim_console.log').read_text();print(name,'sim',[x for x in s.splitlines() if x.startswith(('MEASURE job=0','PASS:','ERROR:','FAIL','MISMATCH'))],flush=True)
  if p.returncode or 'PASS: three consecutive' not in s:continue
 with (d/'results/impl_console.log').open('w') as f:
  p=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/run_impl.tcl','-log','results/impl.log','-journal','results/impl.jou'],cwd=d,stdout=f,stderr=subprocess.STDOUT)
 print(name,'implementation exit',p.returncode,flush=True)
