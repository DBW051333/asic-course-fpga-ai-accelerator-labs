`timescale 1ns/1ps
// Exact paired int8 DSP multipliers, 3 x 64 lanes, 512 useful chunks / 171 cycles.
module fc1_paired #(parameter LANES=192,GROUPS=3,ADDER_LANES=256,DSP_LANES=192,WEIGHTS="",INPUTS="",BIASES="") (
 input wire clk_i,rst_n_i,start_i,ce_i,
 input wire load_bank_i,input_bank_i,
 input wire load_we_i,input wire [5:0] load_addr_i,input wire [63:0] load_data_i,
 output wire ready_o,output reg done_o,
 output reg fc_output_wren_o,output reg [31:0] fc_output_data_o,output reg [6:0] fc_output_addr_o);
 initial if(LANES!=192 || DSP_LANES!=192)$fatal(1,"Dense schedule requires 192 DSP lanes");
 // Three asynchronous read replicas: address {sample_bank,chunk}, depth 16.
 // Each byte position writes only when its containing 64-bit word arrives.
 // The replicas provide independent reads for chunks 6,7,0 and 7,0,1.
 reg active_bank;
 always @(posedge clk_i) if(!rst_n_i)active_bank<=0;
 else if(ce_i && start_i && ready_o)active_bank<=input_bank_i;
 (* rom_style="distributed" *) reg [15:0] biases[0:63];
 initial $readmemh(BIASES,biases);
 reg running;reg [7:0] issue_cycle;
 assign ready_o=rst_n_i && !running;
 reg [LANES*25-1:0] weight_r,weight_q;
 wire [5:0] completion_pair[0:2];wire [2:0] completion;
 wire signed [22:0] snapshot0[0:2],snapshot1[0:2];
 generate if(1)begin:address_bank0
  (* rom_style="block" *) reg [399:0] local_weights[0:170];
  initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_192/data/fc1_bank0.mem",local_weights);
  (* dont_touch="yes" *) reg [7:0] local_addr;
  always @(posedge clk_i)if(!rst_n_i || ce_i)begin
   if(local_addr==170)local_addr<=0;else local_addr<=local_addr+1'b1;
   if(!rst_n_i || (start_i && !running))local_addr<=0;
  end
  always @(posedge clk_i)if(ce_i)weight_r[LANES*25-1-0*400 -:400]<=local_weights[local_addr];
 end endgenerate
 generate if(1)begin:address_bank1
  (* rom_style="block" *) reg [399:0] local_weights[0:170];
  initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_192/data/fc1_bank1.mem",local_weights);
  (* dont_touch="yes" *) reg [7:0] local_addr;
  always @(posedge clk_i)if(!rst_n_i || ce_i)begin
   if(local_addr==170)local_addr<=0;else local_addr<=local_addr+1'b1;
   if(!rst_n_i || (start_i && !running))local_addr<=0;
  end
  always @(posedge clk_i)if(ce_i)weight_r[LANES*25-1-1*400 -:400]<=local_weights[local_addr];
 end endgenerate
 generate if(1)begin:address_bank2
  (* rom_style="block" *) reg [399:0] local_weights[0:170];
  initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_192/data/fc1_bank2.mem",local_weights);
  (* dont_touch="yes" *) reg [7:0] local_addr;
  always @(posedge clk_i)if(!rst_n_i || ce_i)begin
   if(local_addr==170)local_addr<=0;else local_addr<=local_addr+1'b1;
   if(!rst_n_i || (start_i && !running))local_addr<=0;
  end
  always @(posedge clk_i)if(ce_i)weight_r[LANES*25-1-2*400 -:400]<=local_weights[local_addr];
 end endgenerate
 generate if(1)begin:address_bank3
  (* rom_style="block" *) reg [399:0] local_weights[0:170];
  initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_192/data/fc1_bank3.mem",local_weights);
  (* dont_touch="yes" *) reg [7:0] local_addr;
  always @(posedge clk_i)if(!rst_n_i || ce_i)begin
   if(local_addr==170)local_addr<=0;else local_addr<=local_addr+1'b1;
   if(!rst_n_i || (start_i && !running))local_addr<=0;
  end
  always @(posedge clk_i)if(ce_i)weight_r[LANES*25-1-3*400 -:400]<=local_weights[local_addr];
 end endgenerate
 generate if(1)begin:address_bank4
  (* rom_style="block" *) reg [399:0] local_weights[0:170];
  initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_192/data/fc1_bank4.mem",local_weights);
  (* dont_touch="yes" *) reg [7:0] local_addr;
  always @(posedge clk_i)if(!rst_n_i || ce_i)begin
   if(local_addr==170)local_addr<=0;else local_addr<=local_addr+1'b1;
   if(!rst_n_i || (start_i && !running))local_addr<=0;
  end
  always @(posedge clk_i)if(ce_i)weight_r[LANES*25-1-4*400 -:400]<=local_weights[local_addr];
 end endgenerate
 generate if(1)begin:address_bank5
  (* rom_style="block" *) reg [399:0] local_weights[0:170];
  initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_192/data/fc1_bank5.mem",local_weights);
  (* dont_touch="yes" *) reg [7:0] local_addr;
  always @(posedge clk_i)if(!rst_n_i || ce_i)begin
   if(local_addr==170)local_addr<=0;else local_addr<=local_addr+1'b1;
   if(!rst_n_i || (start_i && !running))local_addr<=0;
  end
  always @(posedge clk_i)if(ce_i)weight_r[LANES*25-1-5*400 -:400]<=local_weights[local_addr];
 end endgenerate
 generate if(1)begin:address_bank6
  (* rom_style="block" *) reg [399:0] local_weights[0:170];
  initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_192/data/fc1_bank6.mem",local_weights);
  (* dont_touch="yes" *) reg [7:0] local_addr;
  always @(posedge clk_i)if(!rst_n_i || ce_i)begin
   if(local_addr==170)local_addr<=0;else local_addr<=local_addr+1'b1;
   if(!rst_n_i || (start_i && !running))local_addr<=0;
  end
  always @(posedge clk_i)if(ce_i)weight_r[LANES*25-1-6*400 -:400]<=local_weights[local_addr];
 end endgenerate
 generate if(1)begin:address_bank7
  (* rom_style="block" *) reg [399:0] local_weights[0:170];
  initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_192/data/fc1_bank7.mem",local_weights);
  (* dont_touch="yes" *) reg [7:0] local_addr;
  always @(posedge clk_i)if(!rst_n_i || ce_i)begin
   if(local_addr==170)local_addr<=0;else local_addr<=local_addr+1'b1;
   if(!rst_n_i || (start_i && !running))local_addr<=0;
  end
  always @(posedge clk_i)if(ce_i)weight_r[LANES*25-1-7*400 -:400]<=local_weights[local_addr];
 end endgenerate
 generate if(1)begin:address_bank8
  (* rom_style="block" *) reg [399:0] local_weights[0:170];
  initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_192/data/fc1_bank8.mem",local_weights);
  (* dont_touch="yes" *) reg [7:0] local_addr;
  always @(posedge clk_i)if(!rst_n_i || ce_i)begin
   if(local_addr==170)local_addr<=0;else local_addr<=local_addr+1'b1;
   if(!rst_n_i || (start_i && !running))local_addr<=0;
  end
  always @(posedge clk_i)if(ce_i)weight_r[LANES*25-1-8*400 -:400]<=local_weights[local_addr];
 end endgenerate
 generate if(1)begin:address_bank9
  (* rom_style="block" *) reg [399:0] local_weights[0:170];
  initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_192/data/fc1_bank9.mem",local_weights);
  (* dont_touch="yes" *) reg [7:0] local_addr;
  always @(posedge clk_i)if(!rst_n_i || ce_i)begin
   if(local_addr==170)local_addr<=0;else local_addr<=local_addr+1'b1;
   if(!rst_n_i || (start_i && !running))local_addr<=0;
  end
  always @(posedge clk_i)if(ce_i)weight_r[LANES*25-1-9*400 -:400]<=local_weights[local_addr];
 end endgenerate
 generate if(1)begin:address_bank10
  (* rom_style="block" *) reg [399:0] local_weights[0:170];
  initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_192/data/fc1_bank10.mem",local_weights);
  (* dont_touch="yes" *) reg [7:0] local_addr;
  always @(posedge clk_i)if(!rst_n_i || ce_i)begin
   if(local_addr==170)local_addr<=0;else local_addr<=local_addr+1'b1;
   if(!rst_n_i || (start_i && !running))local_addr<=0;
  end
  always @(posedge clk_i)if(ce_i)weight_r[LANES*25-1-10*400 -:400]<=local_weights[local_addr];
 end endgenerate
 generate if(1)begin:address_bank11
  (* rom_style="block" *) reg [399:0] local_weights[0:170];
  initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_192/data/fc1_bank11.mem",local_weights);
  (* dont_touch="yes" *) reg [7:0] local_addr;
  always @(posedge clk_i)if(!rst_n_i || ce_i)begin
   if(local_addr==170)local_addr<=0;else local_addr<=local_addr+1'b1;
   if(!rst_n_i || (start_i && !running))local_addr<=0;
  end
  always @(posedge clk_i)if(ce_i)weight_r[LANES*25-1-11*400 -:400]<=local_weights[local_addr];
 end endgenerate
 always @(posedge clk_i)if(ce_i)weight_q<=weight_r;
 genvar a,g,byte_lane;generate for(a=0;a<3;a=a+1)begin:array64
  reg [9:0] issue_job;
  wire [511:0] input_chunk;
  for(byte_lane=0;byte_lane<64;byte_lane=byte_lane+1)begin:input_ram
   (* ram_style="distributed" *) reg [7:0] mem[0:15];
   always @(posedge clk_i)if(load_we_i && load_addr_i[2:0]==byte_lane/8)
    mem[{load_bank_i,load_addr_i[5:3]}]<=load_data_i[(byte_lane%8)*8 +:8];
   assign input_chunk[511-byte_lane*8 -:8]=mem[{active_bank,issue_job[2:0]}];
  end
  reg [511:0] input_r,input_q;
  reg signed [24:0] packed_w[0:63];reg signed [7:0] input_p[0:63];
  reg signed [32:0] product_r[0:63];
  reg signed [15:0] low_product[0:63],high_product[0:63];
  wire [1023:0] low_bus,high_bus;wire [31:0] sum0,sum1;
  reg [11:0] valid_pipe;reg [8:0] tag[0:11];
  reg signed [22:0] acc0,acc1,snap0,snap1;
  wire signed [22:0] partial0=sum0[22:0],partial1=sum1[22:0];
  wire first_chunk=tag[11][2:0]<3;
  wire last_chunk=tag[11][2:0]>=5;
  wire signed [22:0] next0=first_chunk?partial0:acc0+partial0;
  wire signed [22:0] next1=first_chunk?partial1:acc1+partial1;
  assign snapshot0[a]=snap0;assign snapshot1[a]=snap1;
  assign completion[a]=valid_pipe[11] && tag[11][2:0]==7;
  assign completion_pair[a]=tag[11][8:3];
  for(g=0;g<64;g=g+1)begin:mult
   (* use_dsp="yes" *) reg signed [32:0] p;
   always @(posedge clk_i)if(ce_i)p<=packed_w[g]*input_p[g];
   assign low_bus[1023-g*16 -:16]=low_product[g];
   assign high_bus[1023-g*16 -:16]=high_product[g];
   always @(posedge clk_i)if(ce_i)begin
    packed_w[g]<=weight_q[LANES*25-1-(a*64+g)*25 -:25];
    input_p[g]<=input_q[511-g*8 -:8];
    product_r[g]<=p;
    low_product[g]<=product_r[g][15:0];
    high_product[g]<=$signed(product_r[g][32:16])+{16'd0,product_r[g][15]};
   end
  end
  adder_tree64 tree0(.clk(clk_i),.rst_n(rst_n_i),.ce_i(ce_i),.data(low_bus),.sum_out(sum0));
  adder_tree64 tree1(.clk(clk_i),.rst_n(rst_n_i),.ce_i(ce_i),.data(high_bus),.sum_out(sum1));
  always @(posedge clk_i)if(ce_i)begin
   input_r<=input_chunk;input_q<=input_r;
   if(valid_pipe[11])begin
    acc0<=next0;acc1<=next1;
    if(last_chunk)begin snap0<=next0;snap1<=next1;end
   end
  end
  integer j;
  always @(posedge clk_i)if(!rst_n_i || ce_i)begin
   if(!rst_n_i)begin issue_job<=a;valid_pipe<=0;end
   else begin
    valid_pipe<={valid_pipe[10:0],running && issue_job<512};
    tag[0]<=issue_job[8:0];for(j=1;j<12;j=j+1)tag[j]<=tag[j-1];
    if(start_i && !running)issue_job<=a;
    else if(running)issue_job<=issue_job+10'd3;
   end
  end
 end endgenerate
 reg merge_pending,merge_valid;
 reg [5:0] merge_pair,result_pair,pair_addr;
 reg signed [22:0] merge00,merge01,merge10,merge11,pair0,pair1;
 reg [1:0] emitting;
 wire [15:0] bias_pair=biases[merge_pair];
 wire signed [22:0] b0={{15{bias_pair[7]}},bias_pair[7:0]};
 wire signed [22:0] b1={{15{bias_pair[15]}},bias_pair[15:8]};
 always @(posedge clk_i)if(ce_i)begin
  if(merge_pending)begin
   merge00<=snapshot0[0]+snapshot0[1];merge01<=snapshot0[2]+b0;
   merge10<=snapshot1[0]+snapshot1[1];merge11<=snapshot1[2]+b1;
  end
  if(merge_valid)begin pair0<=merge00+merge01;pair1<=merge10+merge11;end
 end
 always @(posedge clk_i)if(!rst_n_i || ce_i)begin
  if(!rst_n_i)begin
   running<=0;issue_cycle<=0;merge_pending<=0;merge_valid<=0;
   merge_pair<=0;result_pair<=0;pair_addr<=0;emitting<=0;
   fc_output_wren_o<=0;fc_output_data_o<=0;fc_output_addr_o<=0;done_o<=0;
  end else begin
   if(start_i && !running)begin running<=1;issue_cycle<=0;end
   else if(running)begin
    if(issue_cycle==170)running<=0;else issue_cycle<=issue_cycle+1'b1;
   end
   merge_pending<=|completion;merge_valid<=merge_pending;
   if(completion[0])merge_pair<=completion_pair[0];
   else if(completion[1])merge_pair<=completion_pair[1];
   else if(completion[2])merge_pair<=completion_pair[2];
   if(merge_pending)result_pair<=merge_pair;
   fc_output_wren_o<=0;done_o<=0;
   if(emitting==1)begin
    fc_output_wren_o<=1;fc_output_addr_o<={pair_addr,1'b0};
    fc_output_data_o<=pair0[22]?32'd0:{{9{pair0[22]}},pair0};emitting<=2;
   end else if(emitting==2)begin
    fc_output_wren_o<=1;fc_output_addr_o<={pair_addr,1'b1};
    fc_output_data_o<=pair1[22]?32'd0:{{9{pair1[22]}},pair1};done_o<=pair_addr==63;emitting<=0;
   end
   if(merge_valid)begin pair_addr<=result_pair;emitting<=1;end
  end
 end
endmodule
