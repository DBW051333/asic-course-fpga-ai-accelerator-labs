from pathlib import Path
import shutil
R=Path('/home/ding/vivado_project/Lab6_three_version_comparison');D=R/'original_int8';D.mkdir(exist_ok=True)
for q in ['rtl','tb','tools','results']:(D/q).mkdir(exist_ok=True)
shutil.copytree('/home/ding/vivado_project/Lab6/vivado8',D/'vivado',dirs_exist_ok=True)
(D/'rtl/original_impl_top.v').write_text('''module original_impl_top(input wire clk_i,rst_n_i,start_i,output wire done_o,ready_o,result_valid_o,result_addr_o,output wire [63:0] result_data_o);
wire v1,v2;wire [7:0] d1,d2,d3;wire [6:0] a1;wire [4:0] a2,a3;
assign result_data_o={{56{d3[7]}},d3};assign result_addr_o=a3[0];
reg busy;always @(posedge clk_i)if(!rst_n_i)busy<=0;else if(start_i && !busy)busy<=1;else if(done_o)busy<=0;
assign ready_o=!busy;
lab6_top #(.WIDTH(8)) network(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.input_we_i(1'b0),.input_addr_i(2'd0),.input_data_i(1024'd0),.done_o(done_o),.fc1_wren_o(v1),.fc1_data_o(d1),.fc1_addr_o(a1),.fc2_wren_o(v2),.fc2_data_o(d2),.fc2_addr_o(a2),.fc3_wren_o(result_valid_o),.fc3_data_o(d3),.fc3_addr_o(a3));endmodule
''')
# Latency is from the accepted start edge to observation of second FC3 result, as in optimized TB.
s=Path('/home/ding/vivado_project/Lab6/tb/tb_lab6_top.v').read_text().replace('localparam CLK_PERIOD = 10;','parameter real CLK_PERIOD = 10;')
s=s.replace('/home/ding/vivado_project/Lab6/results/rtl_8.csv',str(D/'results/rtl_8.csv'))
s=s.replace('    lab6_top #','    realtime launched;integer latency_cycles,min_latency=99999,max_latency=0;\n    lab6_top #',1)
s=s.replace('start_i=1;\n','start_i=1; launched=$realtime+CLK_PERIOD/2;\n')
s=s.replace('if (got3==0) score0=$signed(fc3_data);','if(got3==1)begin latency_cycles=$rtoi(($realtime-launched)/CLK_PERIOD+0.5);if(latency_cycles<min_latency)min_latency=latency_cycles;if(latency_cycles>max_latency)max_latency=latency_cycles;end\n            if (got3==0) score0=$signed(fc3_data);')
s=s.replace('        $fclose(result_fd);','        $display("PERFORMANCE latency_cycles=%0d..%0d",min_latency,max_latency);\n        $fclose(result_fd);')
(D/'tb/tb_original.v').write_text(s)
common=f'''set_param general.maxThreads 4
open_project {D}/vivado/Lab6_8.xpr
'''
(D/'tools/run_sim.tcl').write_text(common+f'''remove_files [get_files -of_objects [get_filesets sim_1]]
add_files -fileset sim_1 {D}/tb/tb_original.v
set_property file_type SystemVerilog [get_files *tb_original.v]
set_property top tb_lab6_top [get_filesets sim_1]
set_property generic {{WIDTH=8 CLK_PERIOD=10}} [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
launch_simulation
close_sim -force
exit
''')
(D/'tools/run_synth.tcl').write_text(common+f'''add_files {D}/rtl/original_impl_top.v
set_property top original_impl_top [get_filesets sources_1]
set_property generic {{}} [get_filesets sources_1]
update_compile_order -fileset sources_1
synth_ip [get_ips]
synth_design -top original_impl_top -part xc7z020clg400-1
create_clock -period 4.4 [get_ports clk_i]
write_checkpoint -force {D}/results/synth.dcp
report_utilization -file {D}/results/utilization_synth.rpt
exit
''')
s=Path('/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/tools/run_impl.tcl').read_text().replace('/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual',str(D));(D/'tools/run_impl.tcl').write_text(s)
