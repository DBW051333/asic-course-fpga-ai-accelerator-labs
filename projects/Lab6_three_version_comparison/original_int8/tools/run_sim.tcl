set_param general.maxThreads 4
open_project /home/ding/vivado_project/Lab6_three_version_comparison/original_int8/vivado/Lab6_8.xpr
remove_files [get_files -of_objects [get_filesets sim_1]]
add_files -fileset sim_1 /home/ding/vivado_project/Lab6_three_version_comparison/original_int8/tb/tb_original.v
set_property file_type SystemVerilog [get_files *tb_original.v]
set_property top tb_lab6_top [get_filesets sim_1]
set_property generic {WIDTH=8 CLK_PERIOD=10} [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
launch_simulation
close_sim -force
exit
