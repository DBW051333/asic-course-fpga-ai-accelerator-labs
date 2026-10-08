set script_dir [file dirname [file normalize [info script]]]
set lab5_dir [file normalize [file join $script_dir ..]]
open_project [file join $lab5_dir vivado Lab5.xpr]
reset_run synth_1
launch_runs synth_1 -jobs 2
wait_on_run synth_1
set status [get_property STATUS [get_runs synth_1]]
puts "LAB5_SYNTH_STATUS: $status"
if {![string match "*Complete*" $status]} {
    exit 1
}
open_run synth_1
report_utilization -file [file join $lab5_dir results utilization_synth.rpt]
report_timing_summary -file [file join $lab5_dir results timing_synth.rpt]
exit
