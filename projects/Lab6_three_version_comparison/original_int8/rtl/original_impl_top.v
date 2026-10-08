module original_impl_top(input wire clk_i,rst_n_i,start_i,output wire done_o,ready_o,result_valid_o,result_addr_o,output wire [63:0] result_data_o);
wire v1,v2;wire [7:0] d1,d2,d3;wire [6:0] a1;wire [4:0] a2,a3;
assign result_data_o={{56{d3[7]}},d3};assign result_addr_o=a3[0];
reg busy;always @(posedge clk_i)if(!rst_n_i)busy<=0;else if(start_i && !busy)busy<=1;else if(done_o)busy<=0;
assign ready_o=!busy;
lab6_top #(.WIDTH(8)) network(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.input_we_i(1'b0),.input_addr_i(2'd0),.input_data_i(1024'd0),.done_o(done_o),.fc1_wren_o(v1),.fc1_data_o(d1),.fc1_addr_o(a1),.fc2_wren_o(v2),.fc2_data_o(d2),.fc2_addr_o(a2),.fc3_wren_o(result_valid_o),.fc3_data_o(d3),.fc3_addr_o(a3));endmodule
