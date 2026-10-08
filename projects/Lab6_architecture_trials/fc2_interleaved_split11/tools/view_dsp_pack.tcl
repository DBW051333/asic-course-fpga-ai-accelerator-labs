source [file join [file dirname [info script]] view_pipeline.tcl]
create_wave_config dsp_pair_packing
foreach signal {
 clk pack_weight pack_input pack_result pack_check_valid
 pack_x_used pack_w0_used pack_w1_used
 pack_low_expected pack_low_actual pack_high_raw pack_correction
 pack_high_expected pack_high_actual
} {
 if {$signal in {clk pack_check_valid pack_correction}} {
  add_wave /tb_pipeline/$signal
 } else {
  add_wave -radix dec /tb_pipeline/$signal
 }
}
restart
run 800 ns
