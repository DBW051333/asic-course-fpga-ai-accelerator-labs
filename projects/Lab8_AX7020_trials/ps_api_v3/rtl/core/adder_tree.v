`timescale 1ns/1ps
module adder_tree(input wire clk,rst_n,ce_i,input wire [4095:0] data,output wire [31:0] sum_out);
wire signed [15:0] p[0:255];genvar i;generate for(i=0;i<256;i=i+1)begin:cut_product
wire signed [16:0] rounded=$signed(data[4095-i*16 -:16])+17'sd0;assign p[i]=rounded[15:0];end endgenerate
wire signed [16:0] w0[0:127];generate for(i=0;i<128;i=i+1)begin:a0 assign w0[i]={ p[2*i][15],p[2*i] } + { p[2*i+1][15],p[2*i+1] };end endgenerate
reg signed [16:0] s0[0:127];integer j0;always @(posedge clk) if(ce_i)for(j0=0;j0<128;j0=j0+1)s0[j0]<=w0[j0];
wire signed [17:0] w1[0:63];generate for(i=0;i<64;i=i+1)begin:a1 assign w1[i]={ s0[2*i][16],s0[2*i] } + { s0[2*i+1][16],s0[2*i+1] };end endgenerate
reg signed [17:0] s1[0:63];integer j1;always @(posedge clk) if(ce_i)for(j1=0;j1<64;j1=j1+1)s1[j1]<=w1[j1];
wire signed [18:0] w2[0:31];generate for(i=0;i<32;i=i+1)begin:a2 assign w2[i]={ s1[2*i][17],s1[2*i] } + { s1[2*i+1][17],s1[2*i+1] };end endgenerate
reg signed [18:0] s2[0:31];integer j2;always @(posedge clk) if(ce_i)for(j2=0;j2<32;j2=j2+1)s2[j2]<=w2[j2];
wire signed [19:0] w3[0:15];generate for(i=0;i<16;i=i+1)begin:a3 assign w3[i]={ s2[2*i][18],s2[2*i] } + { s2[2*i+1][18],s2[2*i+1] };end endgenerate
reg signed [19:0] s3[0:15];integer j3;always @(posedge clk) if(ce_i)for(j3=0;j3<16;j3=j3+1)s3[j3]<=w3[j3];
wire signed [20:0] w4[0:7];generate for(i=0;i<8;i=i+1)begin:a4 assign w4[i]={ s3[2*i][19],s3[2*i] } + { s3[2*i+1][19],s3[2*i+1] };end endgenerate
reg signed [20:0] s4[0:7];integer j4;always @(posedge clk) if(ce_i)for(j4=0;j4<8;j4=j4+1)s4[j4]<=w4[j4];
wire signed [21:0] w5[0:3];generate for(i=0;i<4;i=i+1)begin:a5 assign w5[i]={ s4[2*i][20],s4[2*i] } + { s4[2*i+1][20],s4[2*i+1] };end endgenerate
reg signed [21:0] s5[0:3];integer j5;always @(posedge clk) if(ce_i)for(j5=0;j5<4;j5=j5+1)s5[j5]<=w5[j5];
wire signed [22:0] w6[0:1];generate for(i=0;i<2;i=i+1)begin:a6 assign w6[i]={ s5[2*i][21],s5[2*i] } + { s5[2*i+1][21],s5[2*i+1] };end endgenerate
reg signed [22:0] s6[0:1];integer j6;always @(posedge clk) if(ce_i)for(j6=0;j6<2;j6=j6+1)s6[j6]<=w6[j6];
wire signed [23:0] w7[0:0];generate for(i=0;i<1;i=i+1)begin:a7 assign w7[i]={ s6[2*i][22],s6[2*i] } + { s6[2*i+1][22],s6[2*i+1] };end endgenerate
reg signed [23:0] s7[0:0];integer j7;always @(posedge clk) if(ce_i)for(j7=0;j7<1;j7=j7+1)s7[j7]<=w7[j7];
assign sum_out={{8{s7[0][23]}},s7[0]};endmodule
