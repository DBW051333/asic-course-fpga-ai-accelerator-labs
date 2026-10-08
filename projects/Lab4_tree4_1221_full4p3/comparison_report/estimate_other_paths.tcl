open_checkpoint /home/ding/vivado_project/Lab4_parallel64_packed/Lab4.runs/impl_1/fc_top_routed.dcp
set from_regs [get_cells -hier -regexp {.*stage1_reg.*}]
set to_regs [get_cells -hier -regexp {.*stage2_reg.*}]
puts "stage1_regs=[llength $from_regs] stage2_regs=[llength $to_regs]"
set_false_path -from $from_regs -to $to_regs
report_timing -max_paths 10 -file /home/ding/vivado_project/Lab4_parallel64_packed/comparison_report/other_paths.rpt
report_timing_summary -file /home/ding/vivado_project/Lab4_parallel64_packed/comparison_report/other_paths_summary.rpt
