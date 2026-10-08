set_param general.maxThreads 8
open_checkpoint /home/ding/vivado_project/Lab6_bottleneck_optimization/postroute_fanout/results/final_routed.dcp
report_timing_summary -file /home/ding/vivado_project/Lab6_bottleneck_optimization/postroute_fanout/results/timing_verified.rpt
report_route_status -file /home/ding/vivado_project/Lab6_bottleneck_optimization/postroute_fanout/results/route_status_verified.rpt
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
if {$wns < 0 || $whs < 0} {error "Saved checkpoint failed timing"}
close_design
catch {close_project}
create_project Lab6_bottleneck_recommended /home/ding/vivado_project/Lab6_bottleneck_optimization/recommended -part xc7z020clg400-1 -force
set_property target_language Verilog [current_project]
add_files [glob /home/ding/vivado_project/Lab6_bottleneck_optimization/recommended/rtl/*.v]
add_files -fileset constrs_1 /home/ding/vivado_project/Lab6_bottleneck_optimization/recommended/timing.xdc
add_files -fileset sim_1 /home/ding/vivado_project/Lab6_bottleneck_optimization/recommended/tb/tb_quant.v
set_property file_type SystemVerilog [get_files *tb_quant.v]
set_property top lab5_impl_top [get_filesets sources_1]
set_property top tb_quant [get_filesets sim_1]
set_property strategy Performance_Explore [get_runs impl_1]
set_property generic "CLK_PERIOD=4.74" [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
launch_simulation
close_sim
exit
