set root [file normalize [file join [file dirname [info script]] ..]]
set_param general.maxThreads 2
set_param board.repoPaths [list /home/ding/vivado_boards/ax7020_board_files/board_files]
create_project cpu_audit $root/cpu_767_proposal/vivado -part xc7z020clg400-2 -force
set_property board_part alinx.com:ac7020:part0:1.0 [current_project]
create_bd_design cpu_system
set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 processing_system7_0]
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 -config {make_external "FIXED_IO, DDR" apply_board_preset "1" Master "Disable" Slave "Disable"} $ps
set_property -dict [list CONFIG.PCW_APU_PERIPHERAL_FREQMHZ {766.666667} CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {142.857132}] $ps
report_property -all $ps -file $root/cpu_767_proposal/ps_properties.txt
validate_bd_design
save_bd_design
generate_target all [get_files */cpu_system.bd]
write_hw_platform -fixed -force -file $root/cpu_767_proposal/cpu_767.xsa
close_project
exit
