set root [file normalize [file join [file dirname [info script]] ..]]
set_param general.maxThreads 2
open_checkpoint $root/results/final_routed.dcp
set dsps [get_cells -hier -filter {REF_NAME == DSP48E1}]
if {[llength $dsps]!=220} {error "DSP count is not 220"}
foreach cell $dsps {if {[get_property USE_MULT $cell] ne "MULTIPLY"} {error "DSP without multiply: $cell"}}
set softdsps [get_cells -hier -filter {REF_NAME == DSP48E1 && NAME =~ *lut_multiplier*}]
if {[llength $softdsps]!=0} {error "Soft multiplier consumed DSP"}
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
if {$wns<0 || $whs<0} {error "Timing not closed"}
set bad [get_nets -hier -filter {ROUTE_STATUS == UNROUTED || ROUTE_STATUS == PARTIAL || ROUTE_STATUS == CONFLICTS}]
if {[llength $bad]} {error "Unfinished routing"}
report_drc -file $root/results/reopened_drc.rpt
set errors [get_drc_violations -filter {SEVERITY == Error}]
if {[llength $errors]} {error "DRC errors remain"}
set periods [get_property PERIOD [get_clocks]]
if {[llength $periods]!=1 || abs([lindex $periods 0]-7.0)>0.001} {error "Unexpected clocks: $periods"}
set fp [open $root/results/final_checkpoint_audit.json w]
puts $fp "{\"pass\":true,\"dsp\":220,\"soft_dsp\":0,\"wns_ns\":$wns,\"whs_ns\":$whs,\"period_ns\":[lindex $periods 0],\"route_errors\":0,\"drc_errors\":0,\"board_tested\":false}"
close $fp
exit
