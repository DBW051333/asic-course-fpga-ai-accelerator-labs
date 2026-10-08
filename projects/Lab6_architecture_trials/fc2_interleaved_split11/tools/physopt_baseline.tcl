set_param general.maxThreads 8
open_checkpoint /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/baseline_final_routed.dcp
phys_opt_design -directive AggressiveExplore
report_timing_summary -file /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/physopt_baseline_timing.rpt
set orig [get_property PERIOD [get_clocks -of_objects [get_ports clk_i]]]
set slack [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set chosen [expr {ceil(($orig-$slack)*100.0)/100.0}]
create_clock -period $chosen [get_ports clk_i]
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
while {$wns<0} {set chosen [expr {$chosen+0.01}];create_clock -period $chosen [get_ports clk_i];set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]}
set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
report_timing_summary -file /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/physopt_baseline_final.rpt
write_checkpoint -force /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/physopt_baseline_routed.dcp
set fh [open /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/physopt_baseline_clock.json w]
puts $fh [format {{"period": %.3f, "wns": %.3f, "whs": %.3f, "route_target": %.3f}} $chosen $wns $whs $orig];close $fh
exit
