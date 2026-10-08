module lab5_impl_top(input wire clk_i,rst_n_i,start_i,output wire done_o,ready_o,result_valid_o,result_addr_o,output wire [63:0] result_data_o);
 wire v1,v2;wire [7:0] d1;wire [7:0] d2,d2b,d2c,d2d;wire [7:0] d3;wire [6:0] a1;wire [4:0] a2;
 assign result_data_o={{56{d3[7]}},d3};
 lab5_top network(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.ready_o(ready_o),.done_o(done_o),.fc1_wren_o(v1),.fc1_data_o(d1),.fc1_addr_o(a1),
 .fc2_wren_o(v2),.fc2_data_o(d2),.fc2_data_b_o(d2b),.fc2_data_c_o(d2c),.fc2_data_d_o(d2d),.fc2_addr_o(a2),.fc3_wren_o(result_valid_o),.fc3_data_o(d3),.fc3_addr_o(result_addr_o));endmodule
