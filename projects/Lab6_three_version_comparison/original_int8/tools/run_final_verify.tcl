set_param general.maxThreads 4
open_checkpoint /home/ding/vivado_project/Lab6_three_version_comparison/original_int8/results/final_routed.dcp
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
if {$wns<0 || $whs<0} {error "Saved checkpoint failed setup/hold"}
report_timing_summary -file /home/ding/vivado_project/Lab6_three_version_comparison/original_int8/results/timing_verified.rpt
close_design
open_project /home/ding/vivado_project/Lab6_three_version_comparison/original_int8/vivado/Lab6_8.xpr
remove_files [get_files -of_objects [get_filesets sim_1]]
add_files -fileset sim_1 /home/ding/vivado_project/Lab6_three_version_comparison/original_int8/tb/tb_original.v
add_files -fileset sim_1 /home/ding/vivado_project/Lab6_three_version_comparison/original_int8/tb/tb_interval.v
set_property file_type SystemVerilog [get_files *tb_original.v]
set_property file_type SystemVerilog [get_files *tb_interval.v]
set f [open /home/ding/vivado_project/Lab6_three_version_comparison/original_int8/results/final_clock.json r];set j [read $f];close $f
regexp {"period": ([0-9.]+)} $j -> period
set_property generic "WIDTH=8 CLK_PERIOD=$period" [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
set_property top tb_lab6_top [get_filesets sim_1]
launch_simulation
close_sim -force
set_property top tb_original_interval [get_filesets sim_1]
launch_simulation
close_sim -force
exit
