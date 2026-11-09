`timescale 1ns/1ps
// Two exact signed 8x8 products in one DSP25x8 multiply, common input.
module fc1_paired #(parameter LANES=128,GROUPS=4,ADDER_LANES=128,DSP_LANES=128,WEIGHTS="",INPUTS="",BIASES="") (
 input wire clk_i,rst_n_i,start_i,ce_i,
 input wire load_we_i,input wire [5:0] load_addr_i,input wire [63:0] load_data_i,output wire ready_o,output reg done_o,
 output wire [1:0] layer_o,
 output reg fc_output_wren_o,output reg [31:0] fc_output_data_o,fc_output_data_b_o,output reg [6:0] fc_output_addr_o);

 reg [LANES*8-1:0] input_r;
 reg [1:0] layer;assign layer_o=layer;
 reg busy, gap;
 reg [1023:0] features1;
 reg [255:0] features2;

 reg [1:0] issue_group;
 // 32 single-bank input stripes, two groups of 256 INT8 values.
 (* rom_style="distributed" *) reg [15:0] biases[0:127];
 initial $readmemh(BIASES,biases);
 genvar ib;generate for(ib=0;ib<32;ib=ib+1)begin:input_bram
  (* ram_style="block" *) reg [63:0] mem[0:7];
  wire [63:0] ordered={load_data_i[7:0],load_data_i[15:8],load_data_i[23:16],load_data_i[31:24],load_data_i[39:32],load_data_i[47:40],load_data_i[55:48],load_data_i[63:56]};
  wire [1:0] write_group=load_addr_i<32 ? 0 : 1;
  wire write_hit=load_addr_i==ib || load_addr_i==ib+32;
  wire [2:0] write_row={1'b0,write_group};
  wire [63:0] write_data=ordered;
  // Uniform single-address write template, depth padded to 8 for RAM inference.
  always @(posedge clk_i)if(load_we_i && write_hit)mem[write_row]<=write_data;
  always @(posedge clk_i)if(ce_i)input_r[LANES*8-1-ib*64 -:64]<=mem[{1'b0,issue_group}];
 end endgenerate
 reg running;
 assign ready_o=rst_n_i && !busy;reg [$clog2(64*GROUPS)-1:0] issue_addr;reg [5:0] issue_pair;
 reg [LANES*25-1:0] weight_r,weight_q;reg [LANES*8-1:0] input_q;
 reg signed [24:0] packed_w[0:LANES-1];reg signed [7:0] input_p[0:LANES-1];
 wire signed [32:0] product[0:LANES-1];
 reg signed [32:0] product_r[0:LANES-1];
 reg signed [15:0] low_product[0:LANES-1],high_product[0:LANES-1];
 wire [ADDER_LANES*16-1:0] low_bus,high_bus;wire [31:0] sum0,sum1;
 reg [15:0] valid_pipe;reg [7:0] tag[0:15];
 reg signed [22:0] acc0,acc1,pair0,pair1;reg [5:0] pair_addr;reg [1:0] emitting;
 reg signed [22:0] b0_pipe[0:15],b1_pipe[0:15];
 wire last_pair=(layer==0)?(pair_addr==63):(layer==1)?(pair_addr==15):(pair_addr==0);
 wire final_issue=(layer==0)?(issue_addr==127):(layer==1)?(issue_pair==15):1'b1;
 wire issue_enable=running;
 wire [7:0] read_addr=(layer==0)?issue_addr:(layer==1)?(8'd128+issue_pair):8'd144;
 wire [7:0] bias_addr=(layer==0)?{2'b00,issue_pair}:(layer==1)?(8'd64+issue_pair):8'd80;
 wire [7:0] quant_data=(layer==0)?fc_output_data_o[17:10]:(layer==1)?fc_output_data_o[16:9]:fc_output_data_o[15:8];
 wire [7:0] quant_data_b=fc_output_data_b_o[16:9];
 wire [15:0] bias_pair=biases[bias_addr];
 wire signed [22:0] b0={{15{bias_pair[7]}},bias_pair[7:0]};
 wire signed [22:0] b1={{15{bias_pair[15]}},bias_pair[15:8]};
 wire signed [22:0] group_sum0=sum0[22:0],group_sum1=sum1[22:0];
 integer j,bi;
 generate if(LANES/16>0)begin:address_bank0
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank0.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-0*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>1)begin:address_bank1
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank1.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-1*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>2)begin:address_bank2
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank2.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-2*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>3)begin:address_bank3
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank3.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-3*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>4)begin:address_bank4
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank4.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-4*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>5)begin:address_bank5
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank5.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-5*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>6)begin:address_bank6
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank6.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-6*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>7)begin:address_bank7
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank7.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-7*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>8)begin:address_bank8
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank8.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-8*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>9)begin:address_bank9
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank9.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-9*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>10)begin:address_bank10
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank10.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-10*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>11)begin:address_bank11
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank11.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-11*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>12)begin:address_bank12
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank12.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-12*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>13)begin:address_bank13
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank13.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-13*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>14)begin:address_bank14
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank14.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-14*400 -:400]<=local_weights[read_addr];
 end
 end endgenerate
 generate if(LANES/16>15)begin:address_bank15
 (* rom_style="block" *) reg [399:0] local_weights[0:255];
 initial $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/fc1_bank15.mem",local_weights);
 always @(posedge clk_i) if(ce_i)begin
  weight_r[LANES*25-1-15*400 -:400]<=local_weights[read_addr];
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
   always @(posedge clk_i) if(ce_i)begin p<=packed_w[g]*input_p[g];d0<=p;d1<=d0;end
   assign product[g]=d1;
  end else begin
   wire [15:0] y0,y1;
   packed_mul #(.METHOD(2)) lut_multiplier(.clk_i(clk_i),.ce_i(ce_i),.b(packed_w[g]),.x(input_p[g]),.y0(y0),.y1(y1));
   // Both paths have three multiplier registers; product_r supplies the common fourth stage.
   assign product[g]={y1[15],y1,y0};
  end
 end endgenerate
 adder_tree tree0(.clk(clk_i),.rst_n(rst_n_i),.ce_i(ce_i),.data(low_bus),.sum_out(sum0));
 adder_tree tree1(.clk(clk_i),.rst_n(rst_n_i),.ce_i(ce_i),.data(high_bus),.sum_out(sum1));
 always @(posedge clk_i) if(ce_i)begin
  weight_q<=weight_r;
  if(layer==0) input_q<=input_r;
  else if(layer==1) input_q<={features1,1024'd0};
  else input_q<={features2,1792'd0};
  for(bi=0;bi<LANES;bi=bi+1)begin
   packed_w[bi]<=weight_q[LANES*25-1-bi*25 -:25];
   input_p[bi]<=input_q[LANES*8-1-bi*8 -:8];
   product_r[bi]<=product[bi];
   low_product[bi]<=product_r[bi][15:0];
   if(bi<DSP_LANES) high_product[bi]<=$signed(product_r[bi][32:16])+{16'd0,product_r[bi][15]};else high_product[bi]<=product_r[bi][31:16];
  end
  b0_pipe[0]<=b0;b1_pipe[0]<=b1;
  for(bi=1;bi<16;bi=bi+1)begin b0_pipe[bi]<=b0_pipe[bi-1];b1_pipe[bi]<=b1_pipe[bi-1];end
 end
 always @(posedge clk_i) if(!rst_n_i || ce_i) begin
  // Invalid cycles may read any legal address; valid_pipe gates all accumulation.
  if(issue_addr==64*GROUPS-1)issue_addr<=0;else issue_addr<=issue_addr+1'b1;
  if(!rst_n_i)begin running<=0;busy<=0;layer<=0;gap<=0;issue_addr<=0;issue_group<=0;issue_pair<=0;valid_pipe<=0;emitting<=0;fc_output_wren_o<=0;fc_output_data_o<=0;fc_output_data_b_o<=0;fc_output_addr_o<=0;done_o<=0;end
  else begin
   valid_pipe<={valid_pipe[14:0],issue_enable};tag[0]<={issue_pair,issue_group};
   for(j=1;j<16;j=j+1)begin tag[j]<=tag[j-1];end
   if(start_i && !busy)begin running<=1;busy<=1;layer<=0;gap<=0;issue_addr<=0;issue_group<=0;issue_pair<=0;end
   else if(running)begin
    if(layer==0)begin
     if(final_issue)running<=0;
     if(issue_group==GROUPS-1)begin issue_group<=0;issue_pair<=issue_pair+1'b1;end else issue_group<=issue_group+1'b1;
    end else begin
     gap<=0;
     if(final_issue)running<=0;else issue_pair<=issue_pair+1'b1;
    end
   end
   // Save activations directly during emission, no intermediate DMA/reload.
   if(fc_output_wren_o)begin
    if(layer==0)features1[1023-fc_output_addr_o*8 -:8]<=quant_data;
    if(layer==1)features2[255-fc_output_addr_o[4:1]*16 -:16]<={quant_data,quant_data_b};
    if(fc_output_addr_o==((layer==0)?127:(layer==1)?30:1))begin
     if(layer==2)begin busy<=0;done_o<=1;end
     else begin layer<=layer+1'b1;running<=1;gap<=0;issue_pair<=0;issue_group<=0;issue_addr<=0;end
    end
   end
   fc_output_wren_o<=0;done_o<=0;
   if(emitting==1)begin
    fc_output_wren_o<=1;fc_output_addr_o<={pair_addr,1'b0};fc_output_data_o<=(layer!=2 && pair0[22])?32'd0:{{9{pair0[22]}},pair0};
    if(layer==1)begin fc_output_data_b_o<=pair1[22]?32'd0:{{9{pair1[22]}},pair1};emitting<=0;end
    else emitting<=2;
   end else if(emitting==2)begin
    fc_output_wren_o<=1;fc_output_addr_o<={pair_addr,1'b1};fc_output_data_o<=(layer!=2 && pair1[22])?32'd0:{{9{pair1[22]}},pair1};emitting<=0;
   end
   if(valid_pipe[15])begin
    if(tag[15][1:0]==0)begin acc0<=group_sum0+b0_pipe[15];acc1<=group_sum1+b1_pipe[15];end
    else begin acc0<=acc0+group_sum0;acc1<=acc1+group_sum1;end
    if(layer!=0 || tag[15][1:0]==GROUPS-1)begin pair0<=(layer==0)?acc0+group_sum0:group_sum0+b0_pipe[15];pair1<=(layer==0)?acc1+group_sum1:group_sum1+b1_pipe[15];pair_addr<=tag[15][7:2];emitting<=1;end
   end
  end
 end
endmodule
