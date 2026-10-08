module fc1_paired #(parameter LANES=256,GROUPS=2,ADDER_LANES=256,DSP_LANES=200,WEIGHTS="",INPUTS="",BIASES="") (
input wire clk_i,rst_n_i,start_i,output wire ready_o,output reg done_o,fc_output_wren_o,
output reg [31:0] fc_output_data_o,fc_output_data_b_o,output reg [6:0] fc_output_addr_o);
reg [2047:0] inputs[0:1];initial $readmemh(INPUTS,inputs);
wire [2:0] v,r;wire [31:0] data[0:2];wire [6:0] addr[0:2];
reg [22:0] slots[0:5];reg [6:0] base;reg [1:0] emit;reg emitting;
assign ready_o=r[0];
fc1_lane_core #(.LANES(128),.GROUPS(4),.ADDER_LANES(128),.DSP_LANES(128),.WEIGHTS("/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/data/core0"),.BIASES("/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/data/core0_bias.mem")) c0(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.input_vector({inputs[0],inputs[1]}),.ready_o(r[0]),.done_o(),.fc_output_wren_o(v[0]),.fc_output_data_o(data[0]),.fc_output_addr_o(addr[0]));
fc1_lane_core #(.LANES(128),.GROUPS(4),.ADDER_LANES(128),.DSP_LANES(56),.WEIGHTS("/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/data/core1"),.BIASES("/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/data/core1_bias.mem")) c1(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.input_vector({inputs[0],inputs[1]}),.ready_o(r[1]),.done_o(),.fc_output_wren_o(v[1]),.fc_output_data_o(data[1]),.fc_output_addr_o(addr[1]));
fc1_lane_core #(.LANES(128),.GROUPS(4),.ADDER_LANES(128),.DSP_LANES(0),.WEIGHTS("/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/data/core2"),.BIASES("/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/data/core2_bias.mem")) c2(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.input_vector({inputs[0],inputs[1]}),.ready_o(r[2]),.done_o(),.fc_output_wren_o(v[2]),.fc_output_data_o(data[2]),.fc_output_addr_o(addr[2]));
integer j;always @(posedge clk_i)begin
 if(!rst_n_i)begin emitting<=0;emit<=0;done_o<=0;fc_output_wren_o<=0;fc_output_addr_o<=0;fc_output_data_o<=0;fc_output_data_b_o<=0;end
 else begin
  done_o<=0;fc_output_wren_o<=0;
  if(v[0])begin
   for(j=0;j<3;j=j+1)slots[2*j+addr[0][0]]<=data[j][22:0];
   if(addr[0][0])begin base<=addr[0][6:1]*6;emitting<=1;emit<=0;end
  end
  if(emitting)begin
   fc_output_wren_o<=1;fc_output_addr_o<=base+2*emit;
   fc_output_data_o<={9'd0,slots[2*emit]};fc_output_data_b_o<={9'd0,slots[2*emit+1]};
   if(emit==2 || base==126)begin emitting<=0;done_o<=base==126;end
   else emit<=emit+1'b1;
  end
 end
end endmodule