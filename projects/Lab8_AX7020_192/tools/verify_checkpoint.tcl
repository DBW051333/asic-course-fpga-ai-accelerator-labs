set root [file normalize [file join [file dirname [info script]] ..]]
set_param general.maxThreads 2
open_checkpoint $root/results/final_routed.dcp
set maxpath [get_timing_paths -delay_type max -max_paths 1]
set minpath [get_timing_paths -delay_type min -max_paths 1]
set wns [get_property SLACK $maxpath]
set whs [get_property SLACK $minpath]
if {$wns<0 || $whs<0} {error "Saved checkpoint timing failed: $wns/$whs"}
set clock_period [get_property PERIOD [get_clocks clk_fpga_0]]
if {$clock_period != 7.0} {error "Unexpected clock period $clock_period"}
report_drc -file $root/results/checkpoint_drc.rpt
set fatal_drc [get_drc_violations -filter {SEVERITY == Error || SEVERITY == {Critical Warning}}]
if {[llength $fatal_drc]} {error "Fatal DRC: $fatal_drc"}
set ce_bufg [get_drc_violations -filter {NAME =~ DPBU-1*}]
if {[llength $ce_bufg]} {error "Unexpected control-net clock buffers: $ce_bufg"}
report_route_status -file $root/results/route_status.rpt
set route_status [report_route_status -return_string]
if {![regexp {# of routable nets[. ]*: *([0-9]+)} $route_status -> routable]} {error "Route total missing"}
if {![regexp {# of fully routed nets[. ]*: *([0-9]+)} $route_status -> fully_routed]} {error "Route complete count missing"}
if {![regexp {# of nets with routing errors[. ]*: *([0-9]+)} $route_status -> route_errors]} {error "Route errors count missing"}
if {$routable != $fully_routed || $route_errors != 0} {error "Incomplete routing"}
if {[llength [get_clocks]] != 1} {error "Unexpected additional clock"}
source $root/tools/audit_dsp.tcl
source $root/tools/audit_fc2.tcl

set out [open $root/results/checkpoint_verified.json w]
puts $out "{\"pass\":true,\"wns_ns\":$wns,\"whs_ns\":$whs,\"period_ns\":$clock_period,\"error_or_critical_drc\":0,\"control_buffer_warnings\":0}"
close $out
exit
