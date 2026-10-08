open_project /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/vivado/stream_pair256_burst_exact23_tree7_clk4p8.xpr
open_run impl_1
set original_period [get_property PERIOD [get_clocks -of_objects [get_ports clk_i]]]
set original_wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set chosen [expr {ceil(($original_period-$original_wns)*100)/100.0}]
create_clock -period $chosen [get_ports clk_i]
report_timing_summary -file /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/results/timing_final.rpt
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
set fh [open /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/results/final_clock.json w]
puts $fh [format {{"period": %.3f, "wns": %.3f, "whs": %.3f, "route_target": %.3f}} $chosen $wns $whs $original_period]
close $fh
write_checkpoint -force /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/results/final_routed.dcp
set fh [open /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/results/final_clock.xdc w];puts $fh "create_clock -period $chosen \[get_ports clk_i\]";close $fh
create_clock -period [expr {$chosen-0.01}] [get_ports clk_i]
report_timing_summary -file /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/results/timing_boundary.rpt
create_clock -period $chosen [get_ports clk_i]
exit
