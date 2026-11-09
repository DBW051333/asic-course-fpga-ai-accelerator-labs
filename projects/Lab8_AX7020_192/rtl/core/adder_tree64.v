`timescale 1ns/1ps
module adder_tree64(input wire clk,rst_n,ce_i,input wire [1023:0] data,output wire [31:0] sum_out);
wire signed [15:0] p[0:63];
genvar i;generate for(i=0;i<64;i=i+1)begin:leaf assign p[i]=data[1023-i*16 -:16];end endgenerate
wire signed [16:0] w0[0:31];
generate for(i=0;i<32;i=i+1)begin:a0 assign w0[i]={p[2*i][15],p[2*i]}+{p[2*i+1][15],p[2*i+1]};end endgenerate
// Combine levels 0 and 1 within one CE stage, preserving full widths.
wire signed [17:0] w1[0:15];
generate for(i=0;i<16;i=i+1)begin:a1 assign w1[i]={w0[2*i][16],w0[2*i]}+{w0[2*i+1][16],w0[2*i+1]};end endgenerate
reg signed [17:0] s1[0:15];integer j1;always @(posedge clk)if(ce_i)for(j1=0;j1<16;j1=j1+1)s1[j1]<=w1[j1];
wire signed [18:0] w2[0:7];
generate for(i=0;i<8;i=i+1)begin:a2 assign w2[i]={s1[2*i][17],s1[2*i]}+{s1[2*i+1][17],s1[2*i+1]};end endgenerate
reg signed [18:0] s2[0:7];integer j2;always @(posedge clk)if(ce_i)for(j2=0;j2<8;j2=j2+1)s2[j2]<=w2[j2];
wire signed [19:0] w3[0:3];
generate for(i=0;i<4;i=i+1)begin:a3 assign w3[i]={s2[2*i][18],s2[2*i]}+{s2[2*i+1][18],s2[2*i+1]};end endgenerate
reg signed [19:0] s3[0:3];integer j3;always @(posedge clk)if(ce_i)for(j3=0;j3<4;j3=j3+1)s3[j3]<=w3[j3];
wire signed [20:0] w4[0:1];
generate for(i=0;i<2;i=i+1)begin:a4 assign w4[i]={s3[2*i][19],s3[2*i]}+{s3[2*i+1][19],s3[2*i+1]};end endgenerate
reg signed [20:0] s4[0:1];integer j4;always @(posedge clk)if(ce_i)for(j4=0;j4<2;j4=j4+1)s4[j4]<=w4[j4];
wire signed [21:0] w5[0:0];
generate for(i=0;i<1;i=i+1)begin:a5 assign w5[i]={s4[2*i][20],s4[2*i]}+{s4[2*i+1][20],s4[2*i+1]};end endgenerate
reg signed [21:0] s5[0:0];integer j5;always @(posedge clk)if(ce_i)for(j5=0;j5<1;j5=j5+1)s5[j5]<=w5[j5];
// Restore six effective CE edges with a narrow final register.
reg signed [21:0] delayed_sum;
always @(posedge clk)if(ce_i)delayed_sum<=s5[0];
assign sum_out={{10{delayed_sum[21]}},delayed_sum};endmodule
