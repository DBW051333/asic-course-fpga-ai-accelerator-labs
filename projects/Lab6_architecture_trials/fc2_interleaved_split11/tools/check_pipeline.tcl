set_param general.maxThreads 8
create_project pipeline_check /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/simulation_pipeline_check -part xc7z020clg400-1 -force
add_files [glob /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/rtl/*.v]
source /home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/tools/view_pipeline.tcl
close_sim -force
exit
