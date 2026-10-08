from pathlib import Path
import subprocess,json,re,time
r=Path('/home/ding/vivado_project/Lab5_optimization')
for name in ['stream_pair256_dualtail_clk5','stream_pair256_quadtail_clk5','stream_pair256_eighttail_clk5','stream_pair256_quad_tree7_clk4p8']:
 d=r/name;xpr=next((d/'vivado').glob('*.xpr'))
 p=d/'tools/run_impl.tcl';s=p.read_text().replace('-jobs 2','-jobs 1');s='set_param general.maxThreads 4\n'+s
 # Reuse completed synthesis when available.
 run=xpr.parent/(xpr.stem+'.runs')/'synth_1'
 if (run/'lab5_impl_top.dcp').exists() and (run/'.vivado_synth_design.end.rst').exists():
  a=s.index('reset_run synth_1');b=s.index('launch_runs impl_1');s=s[:a]+'reset_run impl_1\n'+s[b:]
 (d/'tools/run_serial_impl.tcl').write_text(s)
 with (d/'results/impl_console.log').open('w') as out:
  c=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/run_serial_impl.tcl','-log','results/impl_serial.log','-journal','results/impl_serial.jou'],cwd=d,stdout=out,stderr=subprocess.STDOUT)
 print(name,'route exit',c.returncode,flush=True)
 if (d/'results/timing_impl.rpt').exists():
  subprocess.run(['python',str(r/'tools/finalize_clock.py'),name],cwd=r)
