open_project /home/ding/vivado_project/Lab4_parallel64_packed/Lab4.xpr
reset_run fc_input_ram_synth_1
reset_run fc_weight_ram_synth_1
reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
open_run synth_1
report_timing_summary -file /home/ding/vivado_project/Lab4_parallel64_packed/comparison_report/timing_synth.rpt
report_utilization -file /home/ding/vivado_project/Lab4_parallel64_packed/comparison_report/utilization_synth.rpt
close_design
reset_run impl_1
launch_runs impl_1 -to_step route_design -jobs 4
wait_on_run impl_1
open_run impl_1
report_timing_summary -file /home/ding/vivado_project/Lab4_parallel64_packed/comparison_report/timing_impl.rpt
report_utilization -file /home/ding/vivado_project/Lab4_parallel64_packed/comparison_report/utilization_impl.rpt
close_project
