set root [file normalize [lindex $argv 0]]
set mode [lindex $argv 1]
set_param general.maxThreads 2
create_project -in_memory -part xc7z020clg400-2
if {$mode == "kernel"} {
 foreach f [lsort [glob $root/rtl/*.v]] {read_verilog -sv $f}
 set top kernel
} else {
 foreach f [lsort [glob $root/rtl/core/*.v]] {read_verilog -sv $f}
 set top lab7_core
}
set fd [open "$root/results/clock.xdc" w]
puts $fd {create_clock -name clk -period 7.000 [get_ports clk_i]}
close $fd
read_xdc "$root/results/clock.xdc"
synth_design -top $top -part xc7z020clg400-2 -mode out_of_context -flatten_hierarchy rebuilt
report_utilization -file "$root/results/synth_utilization.rpt"
report_utilization -hierarchical -file "$root/results/synth_hierarchy.rpt"
if {$mode != "kernel"} {report_utilization -cells [get_cells u_fc1] -file "$root/results/fc1_synth_utilization.rpt"}
report_timing_summary -file "$root/results/synth_timing.rpt"
write_checkpoint -force "$root/results/synth.dcp"
set fp [open "$root/results/primitive_audit.txt" w]
foreach typ {DSP48E1 RAMB36E1 RAMB18E1 CARRY4 LUT1 LUT2 LUT3 LUT4 LUT5 LUT6 LUT6_2 FDRE FDSE} {
 puts $fp "TOTAL $typ [llength [get_cells -hier -filter "REF_NAME == $typ"]]"
 if {$mode != "kernel"} {puts $fp "FC1 $typ [llength [get_cells -hier -filter "REF_NAME == $typ && NAME =~ u_fc1/*"]]"}
}
close $fp
set ndsp [llength [get_cells -hier -filter {REF_NAME == DSP48E1}]]
if {$ndsp > 220} {
 set fp [open "$root/results/not_placeable.txt" w];puts $fp "Needs $ndsp DSP48E1, device has 220. Synthesis only.";close $fp
 exit
}
opt_design
place_design
phys_opt_design
route_design
report_utilization -file "$root/results/routed_utilization.rpt"
report_utilization -hierarchical -file "$root/results/routed_hierarchy.rpt"
if {$mode != "kernel"} {report_utilization -cells [get_cells u_fc1] -file "$root/results/fc1_routed_utilization.rpt"}
report_timing_summary -delay_type min_max -report_unconstrained -file "$root/results/routed_timing.rpt"
report_route_status -file "$root/results/route_status.rpt"
report_drc -file "$root/results/drc.rpt"
write_checkpoint -force "$root/results/routed.dcp"
set fp [open "$root/results/routed_metrics.txt" w]
foreach minmax {max min} {
 set p [get_timing_paths -delay_type $minmax -max_paths 1]
 if {[llength $p]} {puts $fp "$minmax [get_property SLACK $p]"}
}
puts $fp "UNROUTED [llength [get_nets -hier -filter {ROUTE_STATUS == UNROUTED}]]"
puts $fp "ROUTE_ERRORS [llength [get_nets -hier -filter {ROUTE_STATUS == CONFLICTS || ROUTE_STATUS == PARTIAL}]]"
close $fp
exit
