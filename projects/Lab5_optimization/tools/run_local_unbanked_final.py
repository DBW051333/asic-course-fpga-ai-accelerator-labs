from pathlib import Path
import subprocess,time
r=Path('/home/ding/vivado_project/Lab5_optimization')
while not (r/'stream_pair256_banked_exact23_tree7_clk4p8/results/final_clock.json').exists():time.sleep(5)
d=r/'stream_pair256_localinput_unbanked_exact23_tree7_clk4p8'
try:
 while not (d/'results/validation_console.log').exists() or 'PASS: six different' not in (d/'results/validation_console.log').read_text():time.sleep(5)
 p=d/'tools/run_impl.tcl';s='set_param general.maxThreads 4\n'+p.read_text().replace('-jobs 2','-jobs 1');(d/'tools/run_serial_impl.tcl').write_text(s)
 with (d/'results/impl_console.log').open('w') as out:
  c=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/run_serial_impl.tcl','-log','results/impl_serial.log','-journal','results/impl_serial.jou'],cwd=d,stdout=out,stderr=subprocess.STDOUT)
 print('local input route',c.returncode,flush=True)
 if (d/'results/timing_impl.rpt').exists():subprocess.run(['python',str(r/'tools/finalize_clock.py'),d.name],cwd=r)
finally:
 (d/'results/implementation_finished.txt').write_text('completed\n')
 (r/'stream_pair256_localinput_exact23_tree7_clk4p8/results/implementation_finished.txt').write_text('banked local-input trial abandoned; unbanked comparison completed\n')
