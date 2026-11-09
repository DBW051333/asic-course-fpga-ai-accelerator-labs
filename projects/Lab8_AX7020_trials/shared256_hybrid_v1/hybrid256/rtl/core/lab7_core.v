`timescale 1ns/1ps
module lab7_core(input wire clk_i,rst_n_i,start_i,ce_i,
 input wire load_we_i,input wire [5:0] load_addr_i,input wire [63:0] load_data_i,output wire done_o,ready_o,
 output wire fc1_wren_o,output wire [7:0] fc1_data_o,output wire [6:0] fc1_addr_o,
 output wire fc2_wren_o,output wire [7:0] fc2_data_o,fc2_data_b_o,fc2_data_c_o,fc2_data_d_o,output wire [4:0] fc2_addr_o,
 output wire fc3_wren_o,output wire [7:0] fc3_data_o,output wire fc3_addr_o);

 wire v,complete;wire [31:0] value,value_b;wire [6:0] address;wire [1:0] layer;
 wire [7:0] quant=(layer==0)?value[17:10]:(layer==1)?value[16:9]:value[15:8];
 fc1_paired #(.LANES(256),.GROUPS(2),.ADDER_LANES(256),.DSP_LANES(220),
 .BIASES("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/shared_bias.mem")) u_fc1(
 .clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.ce_i(ce_i),.load_we_i(load_we_i),.load_addr_i(load_addr_i),.load_data_i(load_data_i),.done_o(complete),.ready_o(ready_o),.layer_o(layer),.fc_output_wren_o(v),.fc_output_data_o(value),.fc_output_data_b_o(value_b),.fc_output_addr_o(address));
 assign fc1_wren_o=v && layer==0;assign fc1_addr_o=address;assign fc1_data_o=quant;
 wire [7:0] quant_b=value_b[16:9];
 reg [7:0] save0,save1;
 always @(posedge clk_i)if(ce_i && v && layer==1)begin
  if(address[1:0]==0)begin save0<=quant;save1<=quant_b;end
 end
 assign fc2_wren_o=v && layer==1 && address[1:0]==2;
 assign fc2_addr_o={address[4:2],2'b00};
 assign fc2_data_o=save0;assign fc2_data_b_o=save1;assign fc2_data_c_o=quant;assign fc2_data_d_o=quant_b;
 assign fc3_wren_o=v && layer==2;assign fc3_addr_o=address[0];assign fc3_data_o=quant;
 assign done_o=v && layer==2 && address==1;
 endmodule
