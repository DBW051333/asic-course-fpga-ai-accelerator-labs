catch {close_sim -force}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc3_output_ram/sim/fc3_output_ram.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc3_output_ram/sim/fc3_output_ram.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc3_bias_ram/sim/fc3_bias_ram.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc3_bias_ram/sim/fc3_bias_ram.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc3_weight_ram/sim/fc3_weight_ram.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc3_weight_ram/sim/fc3_weight_ram.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc3_input_ram/sim/fc3_input_ram.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc3_input_ram/sim/fc3_input_ram.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc2_output_ram/sim/fc2_output_ram.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc2_output_ram/sim/fc2_output_ram.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc2_bias_ram/sim/fc2_bias_ram.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc2_bias_ram/sim/fc2_bias_ram.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc2_weight_ram/sim/fc2_weight_ram.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc2_weight_ram/sim/fc2_weight_ram.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc2_input_ram/sim/fc2_input_ram.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc2_input_ram/sim/fc2_input_ram.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc_output_ram/sim/fc_output_ram.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc_output_ram/sim/fc_output_ram.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc_bias_ram/sim/fc_bias_ram.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc_bias_ram/sim/fc_bias_ram.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc_weight_ram/sim/fc_weight_ram.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc_weight_ram/sim/fc_weight_ram.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc_input_ram/sim/fc_input_ram.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/fc_input_ram/sim/fc_input_ram.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/comparison/adder_tree_original.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/comparison/adder_tree_original.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/rtl/cut_adder_tree.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/rtl/cut_adder_tree.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/rtl/cut_fc_layer.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/rtl/cut_fc_layer.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/rtl/cut_mult_array.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/rtl/cut_mult_array.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/comparison/fc_original.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/comparison/fc_original.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/rtl/fc1_cut_top.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/rtl/fc1_cut_top.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/rtl/lab5_controller.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/rtl/lab5_controller.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/rtl/lab6_top.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/rtl/lab6_top.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab4/mult_array.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab4/mult_array.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/rtl/output_packer.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/rtl/output_packer.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/cut_mult/sim/cut_mult.vhd}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/cut_mult/sim/cut_mult.vhd}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/mult_8/sim/mult_8.vhd}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.gen/sources_1/ip/mult_8/sim/mult_8.vhd}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/comparison/tb_original_trace.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/comparison/tb_original_trace.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/comparison/tb_current_trace.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/comparison/tb_current_trace.v}}
if {[llength [get_files -quiet {/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/comparison/tb_fc1_compare.v}]] == 0} {add_files -fileset sim_1 {/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/comparison/tb_fc1_compare.v}}
set_property top tb_fc1_compare [get_filesets sim_1]
set_property top_auto_set 0 [get_filesets sim_1]
set_property generic {} [get_filesets sim_1]
set_property xsim.elaborate.debug_level all [get_filesets sim_1]
set_property xsim.elaborate.xelab.more_options { -L blk_mem_gen_v8_4_12 -L xbip_utils_v3_0_15 -L mult_gen_v12_0_24} [get_filesets sim_1]
set_property xsim.simulate.runtime {0ns} [get_filesets sim_1]
set compare_sim_dir [file join [get_property DIRECTORY [current_project]] [get_property NAME [current_project]].sim sim_1 behav xsim]
file mkdir $compare_sim_dir
file copy -force {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.sim/sim_1/behav/xsim/fc_weight_ram.mif} $compare_sim_dir
file copy -force {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.sim/sim_1/behav/xsim/fc3_weight_ram.mif} $compare_sim_dir
file copy -force {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.sim/sim_1/behav/xsim/fc_bias_ram.mif} $compare_sim_dir
file copy -force {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.sim/sim_1/behav/xsim/fc_input_ram.mif} $compare_sim_dir
file copy -force {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.sim/sim_1/behav/xsim/fc3_bias_ram.mif} $compare_sim_dir
file copy -force {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.sim/sim_1/behav/xsim/fc2_weight_ram.mif} $compare_sim_dir
file copy -force {/home/ding/vivado_project/Lab6/vivado8/Lab6_8.sim/sim_1/behav/xsim/fc2_bias_ram.mif} $compare_sim_dir
update_compile_order -fileset sim_1
launch_simulation
create_wave_config fc1_comparison
foreach path {
/tb_fc1_compare/old/clk_i /tb_fc1_compare/old/start_i /tb_fc1_compare/old/relative_cycle
/tb_fc1_compare/old/issue_valid /tb_fc1_compare/old/issue_neuron /tb_fc1_compare/old/issue_group
/tb_fc1_compare/old/fc1_wren /tb_fc1_compare/old/fc1_addr /tb_fc1_compare/old/fc1_data
/tb_fc1_compare/now/start /tb_fc1_compare/now/cycle
/tb_fc1_compare/now/fc1_issue_valid /tb_fc1_compare/now/fc1_issue_pair /tb_fc1_compare/now/fc1_issue_group
/tb_fc1_compare/now/fc1_group_sum0 /tb_fc1_compare/now/fc1_group_sum1
/tb_fc1_compare/now/fc1_pair_result0 /tb_fc1_compare/now/fc1_pair_result1
/tb_fc1_compare/now/fc1_valid /tb_fc1_compare/now/fc1_addr /tb_fc1_compare/now/fc1_data
} {add_wave -radix dec $path}
run 20 us
