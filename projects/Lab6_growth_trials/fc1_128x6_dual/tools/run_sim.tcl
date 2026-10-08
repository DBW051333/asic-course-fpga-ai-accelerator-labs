set_param general.maxThreads 4
create_project validation /home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/simulation -part xc7z020clg400-1 -force
add_files [glob /home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/rtl/*.v]
add_files -fileset sim_1 /home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/tb/tb_quant.v
set_property file_type SystemVerilog [get_files *tb_quant.v]
set_property top tb_quant [get_filesets sim_1]
set_property generic {CLK_PERIOD=4.09} [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
close_sim -force
exit
