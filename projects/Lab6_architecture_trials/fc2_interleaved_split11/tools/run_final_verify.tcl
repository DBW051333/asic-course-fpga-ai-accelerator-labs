open_checkpoint /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/final_routed.dcp
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
if {$wns<0 || $whs<0} {error "Saved checkpoint failed setup/hold"}
report_timing_summary -file /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/timing_verified.rpt
close_design
set_param general.maxThreads 8
 create_project validation /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/simulation_final -part xc7z020clg400-1 -force
 add_files [glob /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/rtl/*.v]
 add_files -fileset sim_1 /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/tb/tb_quant.v
 set_property top lab5_top [get_filesets sources_1]
 set_property file_type SystemVerilog [get_files *tb_quant.v]
 set_property top tb_quant [get_filesets sim_1]
 set_property generic "CLK_PERIOD=4.09" [get_filesets sim_1]
 set_property xsim.simulate.runtime all [get_filesets sim_1]
 update_compile_order -fileset sources_1
 launch_simulation
 close_sim
 exit
