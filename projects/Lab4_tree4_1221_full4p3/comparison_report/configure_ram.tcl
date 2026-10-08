open_project /home/ding/vivado_project/Lab4_parallel64_packed/Lab4.xpr
set_property -dict [list CONFIG.Write_Width_A {512} CONFIG.Write_Depth_A {8} CONFIG.Coe_File {/home/ding/vivado_project/Lab4_parallel64_packed/sel_data_64.coe}] [get_ips fc_input_ram]
set_property -dict [list CONFIG.Write_Width_A {512} CONFIG.Write_Depth_A {1024} CONFIG.Coe_File {/home/ding/vivado_project/Lab4_parallel64_packed/fc1.0.weight_64.coe}] [get_ips fc_weight_ram]
generate_target all [get_ips {fc_input_ram fc_weight_ram}]
add_files -fileset sources_1 [list /home/ding/vivado_project/Lab4_parallel64_packed/sel_data_64.coe /home/ding/vivado_project/Lab4_parallel64_packed/fc1.0.weight_64.coe]
close_project
