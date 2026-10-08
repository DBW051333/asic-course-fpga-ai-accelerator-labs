// Physical implementation exposes final network results. Layer debug buses stay internal.
module lab5_impl_top(input wire clk_i,rst_n_i,start_i,output wire done_o,ready_o,result_valid_o,result_addr_o,output wire [63:0] result_data_o);
wire v1,v2; wire [31:0] d1; wire [47:0] d2;wire [6:0] a1;wire [4:0] a2;
lab5_top network(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.done_o(done_o),.ready_o(ready_o),.fc1_wren_o(v1),.fc1_data_o(d1),.fc1_addr_o(a1),.fc2_wren_o(v2),.fc2_data_o(d2),.fc2_addr_o(a2),.fc3_wren_o(result_valid_o),.fc3_data_o(result_data_o),.fc3_addr_o(result_addr_o));
endmodule
