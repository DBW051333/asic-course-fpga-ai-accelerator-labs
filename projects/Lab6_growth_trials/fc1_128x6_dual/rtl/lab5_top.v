module lab5_top(input wire clk_i,rst_n_i,start_i,output wire done_o,ready_o,
 output wire fc1_wren_o,output wire [7:0] fc1_data_o,output wire [6:0] fc1_addr_o,
 output wire fc2_wren_o,output wire [7:0] fc2_data_o,fc2_data_b_o,fc2_data_c_o,fc2_data_d_o,output wire [4:0] fc2_addr_o,
 output wire fc3_wren_o,output wire [7:0] fc3_data_o,output wire fc3_addr_o);
 wire d1,d2;wire [31:0] full1b;wire [7:0] fc1_data_b;wire [31:0] full1;wire [22:0] full2,full2b,full2c,full2d;wire [20:0] full3;
 fc1_paired #(.LANES(256),.GROUPS(2),.ADDER_LANES(256),.DSP_LANES(200),
 .WEIGHTS("/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/data/fc1_prepacked.mem"),.INPUTS("/home/ding/vivado_project/Lab5_optimization/data/stream_pair256_hybrid_inputs.mem"),.BIASES("/home/ding/vivado_project/Lab5_optimization/data/fc1_paired_bias.mem"))
 u_fc1(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.done_o(d1),.ready_o(ready_o),.fc_output_wren_o(fc1_wren_o),.fc_output_data_o(full1),.fc_output_data_b_o(full1b),.fc_output_addr_o(fc1_addr_o));
 quantize_signed #(.IW(32),.OW(8),.SHIFT(10),.ROUND(0),.SAT(0)) q1(.data_i(full1),.data_o(fc1_data_o));
 quantize_signed #(.IW(32),.OW(8),.SHIFT(10),.ROUND(0),.SAT(0)) q1b(.data_i(full1b),.data_o(fc1_data_b));
 fc_stream_pair_output #(.IW(8),.NI(64),.NO(32),.AW(21),.OW(23),.IA(6),.OA(5),.RELU(1),
 .WEIGHT_FILE("/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/data/fc2_packed_weights.mem"),.BIAS_FILE("/home/ding/vivado_project/Lab5_optimization/data/fc2_bias.mem"))
 u_fc2(.clk_i(clk_i),.rst_n_i(rst_n_i),.valid_i(fc1_wren_o),.data_i(fc1_data_o),.data_b_i(fc1_data_b),.addr_i(fc1_addr_o[6:1]),.valid_o(fc2_wren_o),
 .data_o(full2),.data_b_o(full2b),.data_c_o(full2c),.data_d_o(full2d),.addr_o(fc2_addr_o),.done_o(d2));
 quantize_signed #(.IW(23),.OW(8),.SHIFT(9),.ROUND(0),.SAT(0)) q2(.data_i(full2),.data_o(fc2_data_o));
 quantize_signed #(.IW(23),.OW(8),.SHIFT(9),.ROUND(0),.SAT(0)) q2b(.data_i(full2b),.data_o(fc2_data_b_o));
 quantize_signed #(.IW(23),.OW(8),.SHIFT(9),.ROUND(0),.SAT(0)) q2c(.data_i(full2c),.data_o(fc2_data_c_o));
 quantize_signed #(.IW(23),.OW(8),.SHIFT(9),.ROUND(0),.SAT(0)) q2d(.data_i(full2d),.data_o(fc2_data_d_o));
 fc_stream_two_inputs #(.IW(8),.NI(8),.NO(2),.AW(19),.OW(21),.IA(3),.OA(1),.RELU(0),
 .WEIGHT_FILE("/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/data/fc3_packed_weights.mem"),.BIAS_FILE("/home/ding/vivado_project/Lab5_optimization/data/fc3_bias.mem"))
 u_fc3(.clk_i(clk_i),.rst_n_i(rst_n_i),.valid_i(fc2_wren_o),.data_i(fc2_data_o),.data_b_i(fc2_data_b_o),.data_c_i(fc2_data_c_o),.data_d_i(fc2_data_d_o),
 .addr_i(fc2_addr_o[4:2]),.valid_o(fc3_wren_o),.data_o(full3),.addr_o(fc3_addr_o),.done_o(done_o));
 quantize_signed #(.IW(21),.OW(8),.SHIFT(8),.ROUND(0),.SAT(0)) q3(.data_i(full3),.data_o(fc3_data_o));
 endmodule
