# 从现有 Lab4 RTL 和 Lab5 数据自动创建可仿真的 Vivado 工程。
set script_dir [file dirname [file normalize [info script]]]
set lab5_dir [file normalize [file join $script_dir ..]]
set root_dir [file normalize [file join $lab5_dir ..]]
set lab4_dir [file join $root_dir Lab4]
set proj_dir [file join $lab5_dir vivado]

file mkdir $proj_dir
create_project Lab5 $proj_dir -part xc7z020clg400-1 -force
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]

proc make_bram {name width depth coe mode use_rsta} {
    create_ip -name blk_mem_gen -vendor xilinx.com -library ip -module_name $name
    set cfg [list \
        CONFIG.Memory_Type {Single_Port_RAM} \
        CONFIG.Write_Width_A $width \
        CONFIG.Write_Depth_A $depth \
        CONFIG.Operating_Mode_A $mode \
        CONFIG.Enable_A {Always_Enabled} \
        CONFIG.Register_PortA_Output_of_Memory_Primitives {true} \
        CONFIG.Register_PortA_Output_of_Memory_Core {true} \
        CONFIG.Use_RSTA_Pin $use_rsta]
    if {$coe ne ""} {
        lappend cfg CONFIG.Load_Init_File {true} CONFIG.Coe_File $coe
    }
    set_property -dict $cfg [get_ips $name]
    generate_target all [get_ips $name]
}

# FC1：和已验证 Lab4 相同的 IP 尺寸、读延迟和 COE 数据。
make_bram fc_input_ram  1024 4   [file join $lab5_dir data input sel_data_128.coe] READ_FIRST true
make_bram fc_weight_ram 1024 512 [file join $lab5_dir data params fc1_weight_128.coe] READ_FIRST false
make_bram fc_bias_ram   8    128 [file join $lab5_dir data params fc1.0.bias.coe] READ_FIRST true
make_bram fc_output_ram 32   128 "" WRITE_FIRST false

# FC2：32 路 32-bit 特征图乘 8-bit 权重，四组求和，输出保留 48 位。
make_bram fc2_input_ram  1024 4   "" READ_FIRST false
make_bram fc2_weight_ram 256  128 [file join $lab5_dir data params fc2_weight_32.coe] READ_FIRST false
make_bram fc2_bias_ram   8    32  [file join $lab5_dir data params fc2.0.bias.coe] READ_FIRST false
make_bram fc2_output_ram 48   32  "" WRITE_FIRST false

# FC3：32 路 48-bit 特征图乘 8-bit 权重，输出保留 64 位且没有 ReLU。
make_bram fc3_input_ram  1536 2 "" READ_FIRST false
make_bram fc3_weight_ram 256  2 [file join $lab5_dir data params fc3_weight_32.coe] READ_FIRST false
make_bram fc3_bias_ram   8    2 [file join $lab5_dir data params fc3.bias.coe] READ_FIRST false
make_bram fc3_output_ram 64   2 "" WRITE_FIRST false

create_ip -name mult_gen -vendor xilinx.com -library ip -module_name mult_8
set_property -dict [list \
    CONFIG.PortAType {Signed} CONFIG.PortAWidth {8} \
    CONFIG.PortBType {Signed} CONFIG.PortBWidth {8} \
    CONFIG.Multiplier_Construction {Use_Mults} CONFIG.PipeStages {3} \
    CONFIG.SyncClear {true}] [get_ips mult_8]
generate_target all [get_ips mult_8]

# FC2、FC3 位宽不同，各自使用独立的乘法器 IP 和乘法器阵列。
create_ip -name mult_gen -vendor xilinx.com -library ip -module_name fc2_mult_32x8
set_property -dict [list \
    CONFIG.PortAType {Signed} CONFIG.PortAWidth {32} \
    CONFIG.PortBType {Signed} CONFIG.PortBWidth {8} \
    CONFIG.Multiplier_Construction {Use_Mults} CONFIG.PipeStages {3} \
    CONFIG.SyncClear {true}] [get_ips fc2_mult_32x8]
generate_target all [get_ips fc2_mult_32x8]

create_ip -name mult_gen -vendor xilinx.com -library ip -module_name fc3_mult_48x8
set_property -dict [list \
    CONFIG.PortAType {Signed} CONFIG.PortAWidth {48} \
    CONFIG.PortBType {Signed} CONFIG.PortBWidth {8} \
    CONFIG.Multiplier_Construction {Use_Mults} CONFIG.PipeStages {3} \
    CONFIG.SyncClear {true}] [get_ips fc3_mult_48x8]
generate_target all [get_ips fc3_mult_48x8]

add_files [list \
    [file join $lab4_dir Lab4.srcs sources_1 new adder_tree.v] \
    [file join $lab4_dir fc.v] \
    [file join $lab4_dir mult_array.v] \
    [file join $lab4_dir fc_top.v] \
    [file join $lab5_dir rtl fc2_adder_tree.v] \
    [file join $lab5_dir rtl fc2_mult_array.v] \
    [file join $lab5_dir rtl fc2.v] \
    [file join $lab5_dir rtl fc3_adder_tree.v] \
    [file join $lab5_dir rtl fc3_mult_array.v] \
    [file join $lab5_dir rtl fc3.v] \
    [file join $lab5_dir rtl output_packer.v] \
    [file join $lab5_dir rtl lab5_controller.v] \
    [file join $lab5_dir rtl lab5_top.v]]
add_files -fileset sim_1 [file join $lab5_dir tb tb_lab5_top.v]
set_property top lab5_top [get_filesets sources_1]
set_property top tb_lab5_top [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
launch_simulation
run all
close_sim
exit
