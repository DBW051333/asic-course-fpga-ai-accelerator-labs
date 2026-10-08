# Source this file from the existing project's Vivado Tcl Console.
catch {close_sim -force}
set pipeline_root [file normalize [file join [file dirname [info script]] ..]]
set pipeline_tb [file join $pipeline_root tb tb_pipeline.v]
if {[llength [get_files -quiet $pipeline_tb]] == 0} {
    add_files -fileset sim_1 $pipeline_tb
}
set_property file_type SystemVerilog [get_files $pipeline_tb]
set_property top tb_pipeline [get_filesets sim_1]
set_property top_auto_set 0 [get_filesets sim_1]
set_property generic {CLK_PERIOD=4.09} [get_filesets sim_1]
set_property xsim.elaborate.debug_level all [get_filesets sim_1]
set_property xsim.simulate.runtime {0ns} [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
create_wave_config pipeline_view
set pipeline_signals {
    clk reset_n start cycle
    fc1_issue_valid fc1_issue_pair fc1_issue_group
    fc1_group_valid fc1_compute_pair fc1_compute_group fc1_group_sum0 fc1_group_sum1
    fc1_acc0 fc1_acc1 fc1_pair_result0 fc1_pair_result1
    fc1_valid fc1_addr fc1_data
    fc2_sum_write data_step_valid data_input_index expected_x0 expected_w0 expected_product0 observed_product0 expected_even0 expected_odd0 fc2_even0 fc2_odd0 fc2_merge fc2_snapshot fc2_result0
    fc2_valid fc2_addr fc2_data0 fc2_data1 fc2_data2 fc2_data3
    fc3_sum_write fc3_sum0 fc3_valid fc3_addr fc3_data done
}
foreach pipeline_signal $pipeline_signals {
    if {$pipeline_signal in {fc1_issue_pair fc1_issue_group fc1_compute_pair fc1_compute_group cycle fc1_addr fc2_addr fc3_addr data_input_index}} {
        add_wave -radix unsigned /tb_pipeline/$pipeline_signal
    } elseif {$pipeline_signal in {fc1_group_sum0 fc1_group_sum1 fc1_acc0 fc1_acc1 fc1_pair_result0 fc1_pair_result1 fc1_data fc2_data0 fc2_data1 fc2_data2 fc2_data3 fc3_data expected_x0 expected_w0 expected_product0 observed_product0 expected_even0 expected_odd0 fc2_even0 fc2_odd0 fc2_result0 fc3_sum0}} {
        add_wave -radix dec /tb_pipeline/$pipeline_signal
    } else {
        add_wave /tb_pipeline/$pipeline_signal
    }
}
run 800 ns
