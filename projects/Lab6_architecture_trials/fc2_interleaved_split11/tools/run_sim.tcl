set_param general.maxThreads 8
 create_project validation /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/simulation -part xc7z020clg400-1 -force
 add_files [glob /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/rtl/*.v]
 add_files -fileset sim_1 /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/tb/tb_quant.v
 set_property top lab5_top [get_filesets sources_1]
 set_property file_type SystemVerilog [get_files *tb_quant.v]
 set_property top tb_quant [get_filesets sim_1]
 set_property xsim.simulate.runtime all [get_filesets sim_1]
 update_compile_order -fileset sources_1
 launch_simulation
 close_sim
 exit
