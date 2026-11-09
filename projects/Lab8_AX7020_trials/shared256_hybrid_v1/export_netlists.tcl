set root [file normalize [lindex $argv 0]]
set_param general.maxThreads 1
foreach name [lrange $argv 1 end] {
 open_checkpoint "$root/$name/results/routed.dcp"
 write_verilog -force -mode funcsim "$root/$name/results/core_funcsim.v"
 set fp [open "$root/$name/results/final_dsp_audit.txt" w]
 foreach c [get_cells -hier -filter {REF_NAME == DSP48E1}] {puts $fp "[get_property NAME $c] [get_property USE_MULT $c]"}
 close $fp
 close_design
}
exit
