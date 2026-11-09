# One targeted post-route optimization, preserving the 7 ns clock and RTL.
set root [file normalize [file join [file dirname [info script]] ..]]
set before_wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set before_whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
report_timing_summary -delay_type min_max -file $root/results/first_route_timing.rpt
report_timing -delay_type max -max_paths 10 -file $root/results/first_route_critical_paths.rpt
set physical_repair [expr {$before_wns<0 || $before_whs<0}]
if {$before_wns<0 || $before_whs<0} {
 phys_opt_design -directive AggressiveExplore
 route_design -directive Explore
}
report_timing_summary -delay_type min_max -report_unconstrained -file lab8_system_wrapper_timing_summary_routed.rpt
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
set f [open $root/results/postroute_repair.json w]
puts $f "{\"before_wns_ns\":$before_wns,\"before_whs_ns\":$before_whs,\"physical_repair\":$physical_repair,\"after_wns_ns\":$wns,\"after_whs_ns\":$whs}"
close $f
if {$wns<0 || $whs<0} {error "Post-route optimization did not close timing: $wns / $whs"}
# open_run impl_1 and exported artifacts must use the optimized routed design.
write_checkpoint -force lab8_system_wrapper_routed.dcp
