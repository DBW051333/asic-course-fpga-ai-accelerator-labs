// Two exact signed 8x8 products in one DSP25x8 multiply, common input.
module fc1_paired #(parameter LANES=128,GROUPS=4,ADDER_LANES=128,DSP_LANES=128,WEIGHTS="",INPUTS="",BIASES="") (
 input wire clk_i,rst_n_i,start_i,output wire ready_o,output reg done_o,
 output reg fc_output_wren_o,output reg [31:0] fc_output_data_o,output reg [6:0] fc_output_addr_o);

 (* rom_style="distributed" *) reg [LANES*8-1:0] inputs[0:GROUPS-1];
 (* rom_style="distributed" *) reg [15:0] biases[0:63];
 initial begin $readmemh(INPUTS,inputs);$readmemh(BIASES,biases);end
 reg running;
 assign ready_o=rst_n_i && !running;reg [$clog2(64*GROUPS)-1:0] issue_addr;reg [1:0] issue_group;reg [5:0] issue_pair;
 reg [LANES*25-1:0] weight_r,weight_q;reg [LANES*8-1:0] input_r,input_q;
 reg signed [24:0] packed_w[0:LANES-1];reg signed [7:0] input_p[0:LANES-1];
 wire signed [32:0] product[0:LANES-1];reg signed [7:0] w0_p[0:LANES-1],w1_p[0:LANES-1];
 reg signed [32:0] product_r[0:LANES-1];
 reg signed [15:0] low_product[0:LANES-1],high_product[0:LANES-1];
 wire [ADDER_LANES*16-1:0] low_bus,high_bus;wire [31:0] sum0,sum1;
 reg [15:0] valid_pipe;reg [7:0] tag[0:15];
 reg signed [22:0] acc0,acc1,pair0,pair1;reg [5:0] pair_addr;reg [1:0] emitting;
 reg signed [22:0] b0_pipe[0:15],b1_pipe[0:15];
 wire [15:0] bias_pair=biases[issue_pair];
 wire signed [22:0] b0={{15{bias_pair[7]}},bias_pair[7:0]};
 wire signed [22:0] b1={{15{bias_pair[15]}},bias_pair[15:8]};
 wire signed [22:0] group_sum0=sum0[22:0],group_sum1=sum1[22:0];
 integer j,bi;
 (* rom_style="distributed" *) reg signed [7:0] nibble_su[0:255];
 integer sn,un;
 initial begin
  for(sn=0;sn<16;sn=sn+1)
   for(un=0;un<16;un=un+1)nibble_su[sn*16+un]=(sn<8?sn:sn-16)*un;
 end
 generate if(LANES/16>0)begin:address_bank0
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank0.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-0*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>1)begin:address_bank1
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank1.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-1*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>2)begin:address_bank2
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank2.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-2*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>3)begin:address_bank3
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank3.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-3*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>4)begin:address_bank4
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank4.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-4*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>5)begin:address_bank5
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank5.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-5*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>6)begin:address_bank6
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank6.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-6*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>7)begin:address_bank7
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank7.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-7*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>8)begin:address_bank8
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank8.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-8*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>9)begin:address_bank9
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank9.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-9*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>10)begin:address_bank10
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank10.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-10*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>11)begin:address_bank11
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank11.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-11*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>12)begin:address_bank12
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank12.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-12*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>13)begin:address_bank13
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank13.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-13*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>14)begin:address_bank14
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank14.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-14*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 generate if(LANES/16>15)begin:address_bank15
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_bank15.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-15*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate
 genvar g;generate for(g=0;g<ADDER_LANES;g=g+1)begin:pack_bus
 if(g<LANES)begin
  assign low_bus[ADDER_LANES*16-1-g*16 -:16]=low_product[g];
  assign high_bus[ADDER_LANES*16-1-g*16 -:16]=high_product[g];
 end else begin
  assign low_bus[ADDER_LANES*16-1-g*16 -:16]=16'd0;
  assign high_bus[ADDER_LANES*16-1-g*16 -:16]=16'd0;
 end
 end
 for(g=0;g<LANES;g=g+1)begin:mult
  if(g<DSP_LANES)begin
   (* use_dsp="yes" *) reg signed [32:0] p;
   reg signed [32:0] d0,d1;
   always @(posedge clk_i)begin p<=packed_w[g]*input_p[g];d0<=p;d1<=d0;end
   assign product[g]=d1;
  end else begin
   wire signed [15:0] result[0:1];
   for(genvar h=0;h<2;h=h+1)begin:half
    wire signed [7:0] w=(h==0)?w0_p[g]:w1_p[g];
    (* use_dsp="no" *) reg [7:0] pp00;
    (* use_dsp="no" *) reg signed [7:0] pp01,pp10,pp11;
    reg signed [8:0] cross_r;
    reg signed [15:0] outer_r,p;
    always @(posedge clk_i)begin
     pp00<=input_p[g][3:0]*w[3:0];
     pp01<=nibble_su[{input_p[g][7:4],w[3:0]}];
     pp10<=nibble_su[{w[7:4],input_p[g][3:0]}];
     pp11<=$signed(input_p[g][7:4])*$signed(w[7:4]);
     cross_r<={pp01[7],pp01}+{pp10[7],pp10};
     outer_r<={8'd0,pp00}+($signed({{8{pp11[7]}},pp11})<<<8);
     p<=outer_r+($signed({{7{cross_r[8]}},cross_r})<<<4);
    end
    assign result[h]=p;
   end
   assign product[g]={result[1][15],result[1],result[0]};
  end
 end endgenerate
 adder_tree tree0(.clk(clk_i),.rst_n(rst_n_i),.data(low_bus),.sum_out(sum0));
 adder_tree tree1(.clk(clk_i),.rst_n(rst_n_i),.data(high_bus),.sum_out(sum1));
 always @(posedge clk_i) begin
  // Invalid cycles may read any legal address; valid_pipe gates all accumulation.
  issue_addr<=issue_addr+1'b1;
  weight_q<=weight_r;input_r<=inputs[issue_group];input_q<=input_r;
  for(j=0;j<LANES;j=j+1)begin
   packed_w[j]<=weight_q[LANES*25-1-j*25 -:25];
   input_p[j]<=input_q[LANES*8-1-j*8 -:8];
   w0_p[j]<=weight_q[LANES*25-9-j*25 -:8];w1_p[j]<=weight_q[LANES*25-1-j*25 -:8];product_r[j]<=product[j];
   low_product[j]<=product_r[j][15:0];
   if(j<DSP_LANES) high_product[j]<=$signed(product_r[j][32:16])+{16'd0,product_r[j][15]};else high_product[j]<=product_r[j][31:16];
  end
  if(!rst_n_i)begin running<=0;issue_addr<=0;issue_group<=0;issue_pair<=0;valid_pipe<=0;emitting<=0;fc_output_wren_o<=0;fc_output_data_o<=0;fc_output_addr_o<=0;done_o<=0;end
  else begin
   valid_pipe<={valid_pipe[14:0],running};tag[0]<={issue_pair,issue_group};
   b0_pipe[0]<=b0;b1_pipe[0]<=b1;
   for(j=1;j<16;j=j+1)begin tag[j]<=tag[j-1];b0_pipe[j]<=b0_pipe[j-1];b1_pipe[j]<=b1_pipe[j-1];end
   if(start_i && !running)begin running<=1;issue_addr<=0;issue_group<=0;issue_pair<=0;end
   else if(running)begin if(issue_addr==64*GROUPS-1)running<=0;if(issue_group==GROUPS-1)begin issue_group<=0;issue_pair<=issue_pair+1'b1;end else issue_group<=issue_group+1'b1;end
   fc_output_wren_o<=0;done_o<=0;
   if(emitting==1)begin
    fc_output_wren_o<=1;fc_output_addr_o<={pair_addr,1'b0};fc_output_data_o<=pair0[22]?32'd0:{{9{pair0[22]}},pair0};emitting<=2;
   end else if(emitting==2)begin
    fc_output_wren_o<=1;fc_output_addr_o<={pair_addr,1'b1};fc_output_data_o<=pair1[22]?32'd0:{{9{pair1[22]}},pair1};done_o<=pair_addr==63;emitting<=0;
   end
   if(valid_pipe[15])begin
    if(tag[15][1:0]==0)begin acc0<=group_sum0+b0_pipe[15];acc1<=group_sum1+b1_pipe[15];end
    else begin acc0<=acc0+group_sum0;acc1<=acc1+group_sum1;end
    if(tag[15][1:0]==GROUPS-1)begin pair0<=acc0+group_sum0;pair1<=acc1+group_sum1;pair_addr<=tag[15][7:2];emitting<=1;end
   end
  end
 end
endmodule
