report_utilization -file $root/results/utilization.rpt
report_timing_summary -delay_type min_max -report_unconstrained -file $root/results/timing_summary.rpt
report_drc -file $root/results/drc.rpt
report_methodology -file $root/results/methodology.rpt
report_clocks -file $root/results/clocks.rpt
check_timing -verbose -file $root/results/check_timing.rpt
report_power -file $root/results/power_default_activity.rpt
write_checkpoint -force $root/results/final_routed.dcp
file copy -force $root/vivado/Lab8.runs/impl_1/lab8_system_wrapper.bit $root/overlay/lab8.bit
file copy -force $root/vivado/Lab8.gen/sources_1/bd/lab8_system/hw_handoff/lab8_system.hwh $root/overlay/lab8.hwh
write_hw_platform -fixed -include_bit -force -file $root/overlay/lab8_ax7020_shared256.xsa
set out [open $root/results/build_complete.txt w]
puts $out "Lab8 complete: [clock format [clock seconds]]"
puts $out "Part [get_property PART [current_project]]"
puts $out "Setup WNS [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]"
puts $out "Hold WHS [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]"
close $out
report_timing -delay_type max -max_paths 10 -file $root/results/critical_paths.rpt
report_utilization -hierarchical -file $root/results/utilization_hierarchical.rpt

source $root/tools/audit_dsp.tcl
