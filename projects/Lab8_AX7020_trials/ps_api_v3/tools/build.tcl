set root [file normalize [file join [file dirname [info script]] ..]]
set mode [expr {[llength $argv] ? [lindex $argv 0] : "all"}]
set_param general.maxThreads 2
set_param board.repoPaths [list /home/ding/vivado_boards/ax7020_board_files/board_files]
create_project Lab8 $root/vivado -part xc7z020clg400-2 -force
set_property board_part alinx.com:ac7020:part0:1.0 [current_project]
set_property target_language Verilog [current_project]
add_files [glob $root/rtl/*.v $root/rtl/core/*.v]
add_files -fileset sim_1 $root/tb/tb_lab8.sv
set_property top tb_lab8 [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
add_files -fileset constrs_1 $root/control_routing.xdc
set_property USED_IN_SYNTHESIS false [get_files $root/control_routing.xdc]
create_bd_design lab8_system
set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 processing_system7_0]
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 -config {make_external "FIXED_IO, DDR" apply_board_preset "1" Master "Disable" Slave "Disable"} $ps
set_property -dict [list CONFIG.PCW_USE_M_AXI_GP0 {1} CONFIG.PCW_USE_S_AXI_HP0 {1} CONFIG.PCW_S_AXI_HP0_DATA_WIDTH {64} CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {142.857132} CONFIG.PCW_EN_CLK1_PORT {0} CONFIG.PCW_USE_FABRIC_INTERRUPT {1} CONFIG.PCW_IRQ_F2P_INTR {1}] $ps
set dma [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_dma:7.1 axi_dma_0]
set_property -dict [list CONFIG.c_include_sg {0} CONFIG.c_addr_width {32} CONFIG.c_m_axi_mm2s_data_width {64} CONFIG.c_m_axi_s2mm_data_width {64} CONFIG.c_m_axis_mm2s_tdata_width {64} CONFIG.c_s_axis_s2mm_tdata_width {64} CONFIG.c_mm2s_burst_size {16} CONFIG.c_s2mm_burst_size {16} CONFIG.c_include_mm2s_dre {1} CONFIG.c_include_s2mm_dre {1} CONFIG.c_sg_length_width {23}] $dma
set npu [create_bd_cell -type module -reference lab8_npu npu_0]
set ctrl [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 control_interconnect]
set_property CONFIG.NUM_MI {2} $ctrl
set mem [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 memory_interconnect]
set_property -dict [list CONFIG.NUM_SI {2} CONFIG.NUM_MI {1}] $mem
set rst [create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 reset_100m]
 # Reset polarity is propagated from FCLK_RESET0_N during BD validation.
set one [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 const_one]
set_property CONFIG.CONST_VAL {1} $one
set irq [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 dma_interrupts]
set_property CONFIG.NUM_PORTS {2} $irq
connect_bd_intf_net [get_bd_intf_pins $ps/M_AXI_GP0] [get_bd_intf_pins $ctrl/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins $ctrl/M00_AXI] [get_bd_intf_pins $dma/S_AXI_LITE]
connect_bd_intf_net [get_bd_intf_pins $ctrl/M01_AXI] [get_bd_intf_pins $npu/S_AXI]
connect_bd_intf_net [get_bd_intf_pins $dma/M_AXI_MM2S] [get_bd_intf_pins $mem/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins $dma/M_AXI_S2MM] [get_bd_intf_pins $mem/S01_AXI]
connect_bd_intf_net [get_bd_intf_pins $mem/M00_AXI] [get_bd_intf_pins $ps/S_AXI_HP0]
connect_bd_intf_net [get_bd_intf_pins $dma/M_AXIS_MM2S] [get_bd_intf_pins $npu/S_AXIS]
connect_bd_intf_net [get_bd_intf_pins $npu/M_AXIS] [get_bd_intf_pins $dma/S_AXIS_S2MM]
connect_bd_net [get_bd_pins $ps/FCLK_CLK0] [get_bd_pins $ps/M_AXI_GP0_ACLK] [get_bd_pins $ps/S_AXI_HP0_ACLK] [get_bd_pins $dma/s_axi_lite_aclk] [get_bd_pins $dma/m_axi_mm2s_aclk] [get_bd_pins $dma/m_axi_s2mm_aclk] [get_bd_pins $npu/aclk] [get_bd_pins $rst/slowest_sync_clk] [get_bd_pins $ctrl/ACLK] [get_bd_pins $ctrl/S00_ACLK] [get_bd_pins $ctrl/M00_ACLK] [get_bd_pins $ctrl/M01_ACLK] [get_bd_pins $mem/ACLK] [get_bd_pins $mem/S00_ACLK] [get_bd_pins $mem/S01_ACLK] [get_bd_pins $mem/M00_ACLK]
connect_bd_net [get_bd_pins $ps/FCLK_RESET0_N] [get_bd_pins $rst/ext_reset_in]
connect_bd_net [get_bd_pins $one/dout] [get_bd_pins $rst/dcm_locked]
connect_bd_net [get_bd_pins $rst/interconnect_aresetn] [get_bd_pins $ctrl/ARESETN] [get_bd_pins $mem/ARESETN]
connect_bd_net [get_bd_pins $rst/peripheral_aresetn] [get_bd_pins $dma/axi_resetn] [get_bd_pins $npu/aresetn] [get_bd_pins $ctrl/S00_ARESETN] [get_bd_pins $ctrl/M00_ARESETN] [get_bd_pins $ctrl/M01_ARESETN] [get_bd_pins $mem/S00_ARESETN] [get_bd_pins $mem/S01_ARESETN] [get_bd_pins $mem/M00_ARESETN]
connect_bd_net [get_bd_pins $dma/mm2s_introut] [get_bd_pins $irq/In0]
connect_bd_net [get_bd_pins $dma/s2mm_introut] [get_bd_pins $irq/In1]
connect_bd_net [get_bd_pins $irq/dout] [get_bd_pins $ps/IRQ_F2P]
assign_bd_address
# Cover the upper DDR/CMA region on the 1 GiB AX7020 for both DMA masters.
foreach space {Data_MM2S Data_S2MM} {
    set seg [get_bd_addr_segs axi_dma_0/$space/SEG_processing_system7_0_HP0_DDR_LOWOCM]
    if {[llength $seg] != 1} {error "Missing DMA DDR segment: $space"}
    set_property range 1G $seg
    set_property offset 0x00000000 $seg
}
set addrout [open $root/results/address_map.txt w]
foreach seg [get_bd_addr_segs -hierarchical] {
    puts $addrout "$seg OFFSET=[get_property OFFSET $seg] RANGE=[get_property RANGE $seg]"
}
close $addrout
report_property -all $ps -file $root/results/ps_properties.txt
validate_bd_design
save_bd_design
write_bd_tcl -force $root/results/lab8_system.tcl
set bd [get_files */lab8_system.bd]
set_property synth_checkpoint_mode None $bd
if {$mode eq "create"} {close_project;exit}
generate_target all $bd
make_wrapper -files $bd -top
add_files $root/vivado/Lab8.gen/sources_1/bd/lab8_system/hdl/lab8_system_wrapper.v
set_property top lab8_system_wrapper [get_filesets sources_1]
update_compile_order -fileset sources_1
# One synthesis job, with cross-boundary optimization for the full system.
set_property STEPS.SYNTH_DESIGN.ARGS.FLATTEN_HIERARCHY rebuilt [get_runs synth_1]
launch_runs synth_1 -jobs 1
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis did not complete"}
add_files -fileset utils_1 $root/tools/postroute_opt.tcl
set_property STEPS.WRITE_BITSTREAM.TCL.PRE $root/tools/postroute_opt.tcl [get_runs impl_1]
launch_runs impl_1 -to_step write_bitstream -jobs 1
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation/bitstream did not complete"}
open_run impl_1
source $root/tools/export_results.tcl
close_project
