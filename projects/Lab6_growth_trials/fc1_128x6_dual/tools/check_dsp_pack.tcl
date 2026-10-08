set_param general.maxThreads 8
create_project pipeline_check /home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/simulation_pipeline_check -part xc7z020clg400-1 -force
add_files [glob /home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/rtl/*.v]
source /home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/tools/view_dsp_pack.tcl
close_sim -force
exit
