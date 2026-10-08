create_project stream_pair256_burst_exact23_tree7_clk4p8 /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/vivado -part xc7z020clg400-1 -force
set_property target_language Verilog [current_project]
add_files [glob /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/rtl/*.v]
add_files -fileset sim_1 /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/tb/tb_lab5_top.v
set_property top lab5_top [get_filesets sources_1]
set_property top tb_lab5_top [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
set fh [open /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/timing.xdc w]; puts $fh {create_clock -period 4.800 [get_ports clk_i]}; close $fh
add_files -fileset constrs_1 /home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/timing.xdc
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
launch_simulation
close_sim
exit
