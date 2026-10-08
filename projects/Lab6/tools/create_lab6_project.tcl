set width [lindex $argv 0]
if {$width ni {4 8}} {error "usage: vivado -mode batch -source create_lab6_project.tcl -tclargs 4|8"}
set script_dir [file dirname [file normalize [info script]]]
set lab6_dir [file normalize [file join $script_dir ..]]
set root_dir [file dirname $lab6_dir]
set lab4_dir [file join $root_dir Lab4]
set proj_dir [file join $lab6_dir vivado$width]
file mkdir $proj_dir
create_project Lab6_$width $proj_dir -part xc7z020clg400-1 -force
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]

proc make_bram {name width depth coe mode use_rsta} {
    create_ip -name blk_mem_gen -vendor xilinx.com -library ip -module_name $name
    set cfg [list CONFIG.Memory_Type {Single_Port_RAM} CONFIG.Write_Width_A $width \
        CONFIG.Write_Depth_A $depth CONFIG.Operating_Mode_A $mode \
        CONFIG.Enable_A {Always_Enabled} \
        CONFIG.Register_PortA_Output_of_Memory_Primitives {true} \
        CONFIG.Register_PortA_Output_of_Memory_Core {true} \
        CONFIG.Use_RSTA_Pin $use_rsta]
    if {$coe ne ""} {lappend cfg CONFIG.Load_Init_File {true} CONFIG.Coe_File $coe}
    set_property -dict $cfg [get_ips $name]
    generate_target all [get_ips $name]
}
make_bram fc_input_ram 1024 4 [file join $lab6_dir data sel_data_128.coe] READ_FIRST true
make_bram fc_weight_ram 1024 512 [file join $lab6_dir data params fc1_weight_128.coe] READ_FIRST false
make_bram fc_bias_ram 8 128 [file join $lab6_dir data params fc1.0.bias.coe] READ_FIRST true
make_bram fc_output_ram $width 128 "" WRITE_FIRST false
make_bram fc2_input_ram [expr {32*$width}] 4 "" READ_FIRST false
make_bram fc2_weight_ram 256 128 [file join $lab6_dir data params fc2_weight_32.coe] READ_FIRST false
make_bram fc2_bias_ram 8 32 [file join $lab6_dir data params fc2.0.bias.coe] READ_FIRST false
make_bram fc2_output_ram $width 32 "" WRITE_FIRST false
make_bram fc3_input_ram [expr {32*$width}] 2 "" READ_FIRST false
make_bram fc3_weight_ram 256 2 [file join $lab6_dir data params fc3_weight_32.coe] READ_FIRST false
make_bram fc3_bias_ram 8 2 [file join $lab6_dir data params fc3.bias.coe] READ_FIRST false
make_bram fc3_output_ram $width 2 "" WRITE_FIRST false

create_ip -name mult_gen -vendor xilinx.com -library ip -module_name mult_8
set_property -dict [list CONFIG.PortAType {Signed} CONFIG.PortAWidth {8} \
    CONFIG.PortBType {Signed} CONFIG.PortBWidth {8} \
    CONFIG.Multiplier_Construction {Use_Mults} CONFIG.PipeStages {3} \
    CONFIG.SyncClear {true}] [get_ips mult_8]
generate_target all [get_ips mult_8]
create_ip -name mult_gen -vendor xilinx.com -library ip -module_name cut_mult
set_property -dict [list CONFIG.PortAType {Signed} CONFIG.PortAWidth $width \
    CONFIG.PortBType {Signed} CONFIG.PortBWidth {8} \
    CONFIG.Multiplier_Construction {Use_Mults} CONFIG.PipeStages {3} \
    CONFIG.SyncClear {true}] [get_ips cut_mult]
generate_target all [get_ips cut_mult]

add_files [list \
    [file join $lab4_dir Lab4.srcs sources_1 new adder_tree.v] \
    [file join $lab4_dir fc.v] \
    [file join $lab4_dir mult_array.v] \
    [file join $lab6_dir rtl fc1_cut_top.v] \
    [file join $lab6_dir rtl cut_mult_array.v] \
    [file join $lab6_dir rtl cut_adder_tree.v] \
    [file join $lab6_dir rtl cut_fc_layer.v] \
    [file join $lab6_dir rtl output_packer.v] \
    [file join $lab6_dir rtl lab5_controller.v] \
    [file join $lab6_dir rtl lab6_top.v]]
add_files -fileset sim_1 [file join $lab6_dir tb tb_lab6_top.v]
set_property top lab6_top [get_filesets sources_1]
set_property top tb_lab6_top [get_filesets sim_1]
set_property generic "WIDTH=$width" [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
launch_simulation
run all
close_sim
exit
