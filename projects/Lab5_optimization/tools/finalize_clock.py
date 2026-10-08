from pathlib import Path
import subprocess,sys
r=Path('/home/ding/vivado_project/Lab5_optimization')
for name in sys.argv[1:]:
 d=r/name;xpr=next((d/'vivado').glob('*.xpr'))
 script=f'''open_project {xpr}
open_run impl_1
set original_period [get_property PERIOD [get_clocks -of_objects [get_ports clk_i]]]
set original_wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set chosen [expr {{ceil(($original_period-$original_wns)*100)/100.0}}]
create_clock -period $chosen [get_ports clk_i]
report_timing_summary -file {d}/results/timing_final.rpt
report_timing -delay_type max -max_paths 32 -file {d}/results/critical_paths.rpt
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
set fh [open {d}/results/final_clock.json w]
puts $fh [format {{{{"period": %.3f, "wns": %.3f, "whs": %.3f, "route_target": %.3f}}}} $chosen $wns $whs $original_period]
close $fh
write_checkpoint -force {d}/results/final_routed.dcp
set fh [open {d}/results/final_clock.xdc w];puts $fh "create_clock -period $chosen \\[get_ports clk_i\\]";close $fh
create_clock -period [expr {{$chosen-0.01}}] [get_ports clk_i]
report_timing_summary -file {d}/results/timing_boundary.rpt
create_clock -period $chosen [get_ports clk_i]
exit
'''
 (d/'tools/finalize_clock.tcl').write_text(script)
 with (d/'results/finalize_console.log').open('w') as out:
  c=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/finalize_clock.tcl','-log','results/finalize.log','-journal','results/finalize.jou'],cwd=d,stdout=out,stderr=subprocess.STDOUT)
 print(name,c.returncode,(d/'results/final_clock.json').read_text() if (d/'results/final_clock.json').exists() else 'FAIL',flush=True)
