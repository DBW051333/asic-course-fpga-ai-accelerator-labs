set_param general.maxThreads 8
 open_checkpoint /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/synth.dcp
 opt_design
 place_design -directive Explore
 phys_opt_design -directive Explore
 route_design -directive Explore
 phys_opt_design -directive AggressiveFanoutOpt
 route_design -directive Explore
 report_utilization -file /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/utilization_impl.rpt
 report_timing_summary -file /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/timing_route_target.rpt
 report_route_status -file /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/route_status.rpt
 report_drc -file /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/drc.rpt
 report_timing -max_paths 10 -file /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/critical_paths.rpt
 set orig [get_property PERIOD [get_clocks -of_objects [get_ports clk_i]]]
 set slack [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
 set chosen [expr {ceil(($orig-$slack)*100.0)/100.0}]
 create_clock -period $chosen [get_ports clk_i]
 set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
 while {$wns<0} {set chosen [expr {$chosen+0.01}];create_clock -period $chosen [get_ports clk_i];set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]}
 set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
 report_timing_summary -file /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/timing_final.rpt
 write_checkpoint -force /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/final_routed.dcp
 set fh [open /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/final_clock.xdc w];puts $fh "create_clock -period $chosen \[get_ports clk_i\]";close $fh
 set fh [open /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/final_clock.json w]
 puts $fh [format {{"period": %.3f, "wns": %.3f, "whs": %.3f, "route_target": %.3f}} $chosen $wns $whs $orig];close $fh
 create_clock -period [expr {$chosen-0.01}] [get_ports clk_i]
 report_timing_summary -file /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/timing_boundary.rpt
 exit
