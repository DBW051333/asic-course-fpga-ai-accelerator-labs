open_project /home/ding/vivado_project/Lab4_tree4_1221_full4p3/Lab4.xpr
reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
reset_run impl_1
launch_runs impl_1 -to_step route_design -jobs 4
wait_on_run impl_1
open_run impl_1
report_timing_summary -file /home/ding/vivado_project/Lab4_tree4_1221_full4p3/experiment_results/timing_impl.rpt
report_utilization -file /home/ding/vivado_project/Lab4_tree4_1221_full4p3/experiment_results/utilization_impl.rpt
close_project
