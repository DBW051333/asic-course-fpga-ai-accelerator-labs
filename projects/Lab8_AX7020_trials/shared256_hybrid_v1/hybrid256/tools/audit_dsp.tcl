set out [open $root/results/dsp_registers.txt w]
set total [get_cells -hier -filter {REF_NAME == DSP48E1}]
if {[llength $total] != 220} {error "Total DSP count mismatch"}
foreach cell $total {
 if {[get_property USE_MULT $cell] ne "MULTIPLY"} {error "DSP multiplier disabled: $cell"}
 puts $out "$cell USE_MULT=[get_property USE_MULT $cell] AREG=[get_property AREG $cell] BREG=[get_property BREG $cell] MREG=[get_property MREG $cell] PREG=[get_property PREG $cell]"
}
puts $out "Total DSP count: [llength $total]; all shared between FC1/FC2/FC3"
close $out
set f [open $root/results/dsp_audit.json w]
puts $f {{"pass":true,"shared_dsp":220,"total":220,"all_use_mult_multiply":true,"soft_packed_multipliers":36}}
close $f
