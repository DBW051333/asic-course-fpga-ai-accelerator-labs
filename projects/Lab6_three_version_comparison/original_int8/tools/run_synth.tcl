set_param general.maxThreads 4
open_project /home/ding/vivado_project/Lab6_three_version_comparison/original_int8/vivado/Lab6_8.xpr
add_files /home/ding/vivado_project/Lab6_three_version_comparison/original_int8/rtl/original_impl_top.v
set_property top original_impl_top [get_filesets sources_1]
set_property generic {} [get_filesets sources_1]
update_compile_order -fileset sources_1
synth_ip [get_ips]
synth_design -top original_impl_top -part xc7z020clg400-1
create_clock -period 4.4 [get_ports clk_i]
write_checkpoint -force /home/ding/vivado_project/Lab6_three_version_comparison/original_int8/results/synth.dcp
report_utilization -file /home/ding/vivado_project/Lab6_three_version_comparison/original_int8/results/utilization_synth.rpt
exit
