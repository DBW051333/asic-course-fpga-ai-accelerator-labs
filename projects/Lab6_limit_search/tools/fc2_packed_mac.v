// Exact paired INT8 MAC. A modulo-wrap counter recovers the low-channel carry.
module fc_stream_pair_output #(
 parameter IW=8, NI=128, NO=32, AW=21, OW=23, IA=7, OA=5, RELU=1,
 parameter WEIGHT_FILE="", BIAS_FILE=""
)(input wire clk_i,rst_n_i,valid_i,
 input wire [IW-1:0] data_i,input wire [IA-1:0] addr_i,
 output reg valid_o,output reg [OW-1:0] data_o,data_b_o,data_c_o,data_d_o,
 output reg [OA-1:0] addr_o,output reg done_o);
 localparam RW=(NO/2)*25;
 (* rom_style="block" *) reg [RW-1:0] weights[0:NI-1];
 reg signed [7:0] biases[0:NO-1];
 initial begin $readmemh(WEIGHT_FILE,weights);$readmemh(BIAS_FILE,biases);end
 reg [RW-1:0] weight_r,weight_d;
 reg signed [IW-1:0] data_r,data_d;
 reg [2:0] valid_pipe,first_pipe,last_pipe;
 reg valid_after,first_after,last_after;
 reg signed [AW-1:0] snapshot[0:NO-1];
 genvar g;
 generate for(g=0;g<NO/2;g=g+1)begin:mac
  wire signed [24:0] w=weight_d[RW-1-g*25 -:25];
  wire signed [47:0] b0={{40{biases[2*g][7]}},biases[2*g]};
  wire signed [47:0] b1={{40{biases[2*g+1][7]}},biases[2*g+1]};
  wire signed [47:0] packed_bias=(b1<<<16)+b0;
  (* use_dsp="yes" *) reg signed [32:0] product;
  (* use_dsp="yes" *) reg signed [47:0] packed_acc;
  reg negative,negative_d;
  reg [15:0] previous_low;
  reg signed [7:0] quotient;
  wire [15:0] low=packed_acc[15:0];
  wire signed [7:0] step=(negative_d && low>previous_low)?-8'sd1:
                          ((!negative_d && low<previous_low)?8'sd1:8'sd0);
  wire signed [7:0] next_q=first_after?(low[15]?-8'sd1:8'sd0):quotient+step;
  wire signed [AW-1:0] exact_low=$signed({next_q,low});
  wire signed [31:0] exact_high=$signed(packed_acc[47:16])-$signed(next_q);
  always @(posedge clk_i)begin
   product<=w*data_d;
   negative<=w[7]^data_d[IW-1];negative_d<=negative;
   if(valid_pipe[2])packed_acc<=(first_pipe[2]?packed_bias:packed_acc)+{{15{product[32]}},product};
   if(!rst_n_i)begin quotient<=0;previous_low<=0;end
   else if(valid_after)begin
    quotient<=next_q;previous_low<=low;
    if(last_after)begin snapshot[2*g]<=exact_low;snapshot[2*g+1]<=exact_high[AW-1:0];end
   end
  end
 end endgenerate
 reg emitting,read_valid;
 reg [OA-1:0] emit_idx,read_addr;
 reg signed [AW-1:0] read_data,read_data_b,read_data_c,read_data_d;
 always @(posedge clk_i)begin
  weight_r<=weights[addr_i];data_r<=data_i;weight_d<=weight_r;data_d<=data_r;
  if(!rst_n_i)begin
   valid_pipe<=0;first_pipe<=0;last_pipe<=0;valid_after<=0;first_after<=0;last_after<=0;
   emitting<=0;read_valid<=0;emit_idx<=0;valid_o<=0;done_o<=0;addr_o<=0;data_o<=0;
  end else begin
   valid_pipe<={valid_pipe[1:0],valid_i};first_pipe<={first_pipe[1:0],addr_i==0};last_pipe<={last_pipe[1:0],addr_i==NI-1};
   valid_after<=valid_pipe[2];first_after<=first_pipe[2];last_after<=last_pipe[2];
   if(valid_after && last_after)begin emitting<=1;emit_idx<=0;end
   read_valid<=emitting;
   if(emitting)begin
    read_data<=snapshot[emit_idx];read_data_b<=snapshot[emit_idx+1'b1];read_data_c<=snapshot[emit_idx+2'd2];read_data_d<=snapshot[emit_idx+3'd3];read_addr<=emit_idx;
    if(emit_idx==NO-4)emitting<=0;else emit_idx<=emit_idx+3'd4;
   end
   valid_o<=read_valid;addr_o<=read_addr;
   data_o<=(RELU && read_data[AW-1])?{OW{1'b0}}:{{(OW-AW){read_data[AW-1]}},read_data};
   data_b_o<=(RELU && read_data_b[AW-1])?{OW{1'b0}}:{{(OW-AW){read_data_b[AW-1]}},read_data_b};
   data_c_o<=(RELU && read_data_c[AW-1])?{OW{1'b0}}:{{(OW-AW){read_data_c[AW-1]}},read_data_c};
   data_d_o<=(RELU && read_data_d[AW-1])?{OW{1'b0}}:{{(OW-AW){read_data_d[AW-1]}},read_data_d};
   done_o<=read_valid && read_addr==NO-4;
  end
 end
endmodule
