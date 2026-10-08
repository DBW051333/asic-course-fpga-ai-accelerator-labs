module adder_tree(input wire clk,rst_n,input wire [2047:0] data,output wire [31:0] sum_out);
wire signed [15:0] p[0:127];genvar i;generate for(i=0;i<128;i=i+1)begin assign p[i]=data[2047-i*16 -:16];end endgenerate
reg signed [16:0] s0[0:63];integer j0;always @(posedge clk)for(j0=0;j0<64;j0=j0+1)s0[j0]<={p[2*j0][15],p[2*j0]}+{p[2*j0+1][15],p[2*j0+1]};
reg signed [17:0] s1[0:31];integer j1;always @(posedge clk)for(j1=0;j1<32;j1=j1+1)s1[j1]<={s0[2*j1][16],s0[2*j1]}+{s0[2*j1+1][16],s0[2*j1+1]};
reg signed [18:0] s2[0:15];integer j2;always @(posedge clk)for(j2=0;j2<16;j2=j2+1)s2[j2]<={s1[2*j2][17],s1[2*j2]}+{s1[2*j2+1][17],s1[2*j2+1]};
reg signed [19:0] s3[0:7];integer j3;always @(posedge clk)for(j3=0;j3<8;j3=j3+1)s3[j3]<={s2[2*j3][18],s2[2*j3]}+{s2[2*j3+1][18],s2[2*j3+1]};
reg signed [20:0] s4[0:3];integer j4;always @(posedge clk)for(j4=0;j4<4;j4=j4+1)s4[j4]<={s3[2*j4][19],s3[2*j4]}+{s3[2*j4+1][19],s3[2*j4+1]};
reg signed [21:0] s5[0:1];integer j5;always @(posedge clk)for(j5=0;j5<2;j5=j5+1)s5[j5]<={s4[2*j5][20],s4[2*j5]}+{s4[2*j5+1][20],s4[2*j5+1]};
reg signed [22:0] s6[0:0];integer j6;always @(posedge clk)for(j6=0;j6<1;j6=j6+1)s6[j6]<={s5[2*j6][21],s5[2*j6]}+{s5[2*j6+1][21],s5[2*j6+1]};
assign sum_out={{9{s6[0][22]}},s6[0]};endmodule