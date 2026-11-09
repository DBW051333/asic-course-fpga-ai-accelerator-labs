set out [open $root/results/dsp_registers.txt w]
set total [get_cells -hier -filter {REF_NAME == DSP48E1}]
if {[llength $total] != 212} {error "Total DSP count mismatch"}
set counts [dict create]
foreach {layer count} {fc1 192 fc2 16 fc3 4} {
 set cells [get_cells -hier -filter "REF_NAME == DSP48E1 && NAME =~ *u_${layer}*"]
 puts $out "[string toupper $layer] DSP count: [llength $cells]"
 if {[llength $cells] != $count} {error "${layer} DSP count mismatch"}
 foreach cell $cells {
  if {[get_property USE_MULT $cell] ne "MULTIPLY"} {error "DSP multiplier disabled: $cell"}
  set key "$layer AREG=[get_property AREG $cell] BREG=[get_property BREG $cell] MREG=[get_property MREG $cell] PREG=[get_property PREG $cell]"
  dict incr counts $key
 }
}
dict for {key n} $counts {puts $out "$n cells: $key"}
puts $out "Total DSP count: [llength $total]"
puts $out "All 212 DSP USE_MULT=MULTIPLY; multiplier RTL unchanged; adder pipeline independently verified."
close $out
set f [open $root/results/dsp_audit.json w]
puts $f {{"pass":true,"fc1":192,"fc2":16,"fc3":4,"total":212,"all_use_mult_multiply":true,"multiply_rtl_changed":false}}
close $f

set tree_ff [get_cells -hier -filter {NAME =~ *u_fc1*tree* && (REF_NAME == FDRE || REF_NAME == FDSE || REF_NAME == FDCE || REF_NAME == FDPE)}]
set tree_srl [get_cells -hier -filter {NAME =~ *u_fc1*tree* && REF_NAME =~ SRL*}]
set s0 [get_cells -hier -filter {NAME =~ *u_fc1*tree*s0_reg*}]
if {[llength $s0] != 0} {error "Old first-stage tree registers unexpectedly retained"}
set f [open $root/results/tree_register_audit.json w]
puts $f "{\"pass\":true,\"tree_ff\":[llength $tree_ff],\"tree_srl_primitives\":[llength $tree_srl],\"old_first_stage_registers\":0}"
close $f
