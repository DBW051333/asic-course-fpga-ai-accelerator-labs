from pathlib import Path
import json,subprocess,time
r=Path('/home/ding/vivado_project/Lab5_optimization')
local=r/'stream_pair256_localinput_exact23_tree7_clk4p8'
if local.exists():
 while not (local/'results/implementation_finished.txt').exists():time.sleep(5)
subprocess.run(['python',str(r/'tools/write_report.py')])
best=json.loads((r/'results/recommended.json').read_text());d=r/best['name'];xpr=next((d/'vivado').glob('*.xpr'))
s=f'''set_param general.maxThreads 4
open_project {xpr}
if {{[llength [get_runs -quiet impl_explore]]==0}} {{create_run impl_explore -parent_run synth_1 -flow [get_property FLOW [get_runs impl_1]] -strategy Performance_Explore -constrset constrs_1}}
reset_run impl_explore
launch_runs impl_explore -to_step route_design -jobs 1
wait_on_run impl_explore
open_run impl_explore
report_utilization -file {d}/results/utilization_explore.rpt
report_timing_summary -file {d}/results/timing_explore.rpt
set original_period [get_property PERIOD [get_clocks -of_objects [get_ports clk_i]]]
set original_wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set chosen [expr {{ceil(($original_period-$original_wns)*100)/100.0}}]
create_clock -period $chosen [get_ports clk_i]
report_timing_summary -file {d}/results/timing_explore_final.rpt
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
set fh [open {d}/results/final_clock_explore.json w]
puts $fh [format {{{{"period": %.3f, "wns": %.3f, "whs": %.3f, "route_target": %.3f, "implementation_run":"impl_explore"}}}} $chosen $wns $whs $original_period]
close $fh
write_checkpoint -force {d}/results/explore_routed.dcp
create_clock -period [expr {{$chosen-0.01}}] [get_ports clk_i]
report_timing_summary -file {d}/results/timing_explore_boundary.rpt
exit
'''
(d/'tools/run_explore.tcl').write_text(s)
with (d/'results/explore_console.log').open('w') as out:
 c=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/run_explore.tcl','-log','results/explore.log','-journal','results/explore.jou'],cwd=d,stdout=out,stderr=subprocess.STDOUT)
print(d.name,c.returncode,flush=True)
f=d/'results/final_clock_explore.json'
if f.exists():
 explore=json.loads(f.read_text());default=json.loads((d/'results/final_clock.json').read_text())
 print(explore,flush=True)
 if explore['period']<default['period'] and explore['wns']>=0 and explore['whs']>=0:
  import shutil
  shutil.copy2(d/'results/final_clock.json',d/'results/final_clock_default.json')
  shutil.copy2(f,d/'results/final_clock.json')
  shutil.copy2(d/'results/timing_final.rpt',d/'results/timing_final_default.rpt')
  shutil.copy2(d/'results/timing_explore_final.rpt',d/'results/timing_final.rpt')
  shutil.copy2(d/'results/timing_explore_boundary.rpt',d/'results/timing_boundary.rpt')
  shutil.copy2(d/'results/explore_routed.dcp',d/'results/final_routed.dcp')
  (d/'results/final_clock.xdc').write_text(f"create_clock -period {explore['period']:.3f} [get_ports clk_i]\n")
  shutil.copy2(d/'results/utilization_impl.rpt',d/'results/utilization_impl_default.rpt')
  shutil.copy2(d/'results/utilization_explore.rpt',d/'results/utilization_impl.rpt')
  print('Explore selected',flush=True)
 else:print('Default retained',flush=True)
subprocess.run(['python',str(r/'tools/write_report.py')])
