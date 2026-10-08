set_param general.maxThreads 4
 create_project fc2_interleaved_split11 /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/vivado -part xc7z020clg400-1 -force
 set_property target_language Verilog [current_project]
 add_files [glob /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/rtl/*.v]
 add_files -fileset constrs_1 /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/timing.xdc
 set_property top lab5_impl_top [get_filesets sources_1]
 update_compile_order -fileset sources_1
 synth_design -top lab5_impl_top -part xc7z020clg400-1
 write_checkpoint -force /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/synth.dcp
 report_utilization -file /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/utilization_synth.rpt
 report_utilization -hierarchical -file /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/utilization_hier_synth.rpt
 report_timing_summary -file /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/timing_synth.rpt
 set fh [open "/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/bram_registers.txt" w]
 foreach c [get_cells -hier -filter {REF_NAME =~ RAMB*}] {
  if {[lsearch -exact [list_property $c] DOA_REG]>=0} {puts $fh "$c DOA_REG=[get_property DOA_REG $c] DOB_REG=[get_property DOB_REG $c]"}
 }
 close $fh
 exit
