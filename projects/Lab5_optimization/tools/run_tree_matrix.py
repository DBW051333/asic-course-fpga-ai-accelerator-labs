from pathlib import Path
import subprocess,re
r=Path('/home/ding/vivado_project/Lab5_optimization')
for name in ['stream_pair256_partial5_clk5','stream_pair256_five_clk5','stream_pair256_3221_clk5']:
 d=r/name
 if not (d/'vivado'/f'{name}.xpr').exists():
  with (d/'results/sim_console.log').open('w') as out:
   subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/create_sim.tcl','-log','results/sim.log','-journal','results/sim.jou'],cwd=d,stdout=out,stderr=subprocess.STDOUT)
 if 'PASS: three consecutive' not in (d/'results/sim_console.log').read_text():
  print(name,'SIM FAIL',flush=True);continue
 with (d/'results/impl_console.log').open('w') as out:
  result=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/run_impl.tcl','-log','results/impl.log','-journal','results/impl.jou'],cwd=d,stdout=out,stderr=subprocess.STDOUT)
 p=d/'results/timing_impl.rpt';m=re.search(r'Slack \([^)]*\)\s*:\s*(-?[\d.]+)ns',p.read_text()) if p.exists() else None
 print(name,result.returncode,m.group(1) if m else 'no timing',flush=True)
