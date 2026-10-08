set_param general.maxThreads 4
open_project /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/vivado/stream_pair256_burst_exact23_tree7_clk4p8.xpr
if {[llength [get_runs -quiet impl_explore]]==0} {create_run impl_explore -parent_run synth_1 -flow [get_property FLOW [get_runs impl_1]] -strategy Performance_Explore -constrset constrs_1}
reset_run impl_explore
launch_runs impl_explore -to_step route_design -jobs 1
wait_on_run impl_explore
open_run impl_explore
report_utilization -file /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/results/utilization_explore.rpt
report_timing_summary -file /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/results/timing_explore.rpt
set original_period [get_property PERIOD [get_clocks -of_objects [get_ports clk_i]]]
set original_wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set chosen [expr {ceil(($original_period-$original_wns)*100)/100.0}]
create_clock -period $chosen [get_ports clk_i]
report_timing_summary -file /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/results/timing_explore_final.rpt
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
set fh [open /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/results/final_clock_explore.json w]
puts $fh [format {{"period": %.3f, "wns": %.3f, "whs": %.3f, "route_target": %.3f, "implementation_run":"impl_explore"}} $chosen $wns $whs $original_period]
close $fh
write_checkpoint -force /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/results/explore_routed.dcp
create_clock -period [expr {$chosen-0.01}] [get_ports clk_i]
report_timing_summary -file /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/results/timing_explore_boundary.rpt
exit
