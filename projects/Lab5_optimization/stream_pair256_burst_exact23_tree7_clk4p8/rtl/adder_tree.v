module adder_tree(input wire clk,rst_n,input wire [4095:0] data,output wire [31:0] sum_out);
wire signed [15:0] p[0:255];
genvar i; generate for(i=0;i<256;i=i+1) begin:u assign p[i]=data[4095-i*16 -:16]; end endgenerate
wire signed [16:0] w0_0[0:127];
generate for(i=0;i<128;i=i+1) begin:a0_0 assign w0_0[i]={ p[2*i][15],p[2*i] } + { p[2*i+1][15],p[2*i+1] }; end endgenerate
wire signed [17:0] w0_1[0:63];
generate for(i=0;i<64;i=i+1) begin:a0_1 assign w0_1[i]={ w0_0[2*i][16],w0_0[2*i] } + { w0_0[2*i+1][16],w0_0[2*i+1] }; end endgenerate
reg signed [17:0] s0[0:63]; integer k0; always @(posedge clk) begin for(k0=0;k0<64;k0=k0+1) s0[k0] <= w0_1[k0]; end
wire signed [18:0] w1_0[0:31];
generate for(i=0;i<32;i=i+1) begin:a1_0 assign w1_0[i]={ s0[2*i][17],s0[2*i] } + { s0[2*i+1][17],s0[2*i+1] }; end endgenerate
reg signed [18:0] s1[0:31]; integer k1; always @(posedge clk) begin for(k1=0;k1<32;k1=k1+1) s1[k1] <= w1_0[k1]; end
wire signed [19:0] w2_0[0:15];
generate for(i=0;i<16;i=i+1) begin:a2_0 assign w2_0[i]={ s1[2*i][18],s1[2*i] } + { s1[2*i+1][18],s1[2*i+1] }; end endgenerate
reg signed [19:0] s2[0:15]; integer k2; always @(posedge clk) begin for(k2=0;k2<16;k2=k2+1) s2[k2] <= w2_0[k2]; end
wire signed [20:0] w3_0[0:7];
generate for(i=0;i<8;i=i+1) begin:a3_0 assign w3_0[i]={ s2[2*i][19],s2[2*i] } + { s2[2*i+1][19],s2[2*i+1] }; end endgenerate
reg signed [20:0] s3[0:7]; integer k3; always @(posedge clk) begin for(k3=0;k3<8;k3=k3+1) s3[k3] <= w3_0[k3]; end
wire signed [21:0] w4_0[0:3];
generate for(i=0;i<4;i=i+1) begin:a4_0 assign w4_0[i]={ s3[2*i][20],s3[2*i] } + { s3[2*i+1][20],s3[2*i+1] }; end endgenerate
reg signed [21:0] s4[0:3]; integer k4; always @(posedge clk) begin for(k4=0;k4<4;k4=k4+1) s4[k4] <= w4_0[k4]; end
wire signed [22:0] w5_0[0:1];
generate for(i=0;i<2;i=i+1) begin:a5_0 assign w5_0[i]={ s4[2*i][21],s4[2*i] } + { s4[2*i+1][21],s4[2*i+1] }; end endgenerate
reg signed [22:0] s5[0:1]; integer k5; always @(posedge clk) begin for(k5=0;k5<2;k5=k5+1) s5[k5] <= w5_0[k5]; end
wire signed [23:0] w6_0[0:0];
generate for(i=0;i<1;i=i+1) begin:a6_0 assign w6_0[i]={ s5[2*i][22],s5[2*i] } + { s5[2*i+1][22],s5[2*i+1] }; end endgenerate
reg signed [23:0] s6[0:0]; integer k6; always @(posedge clk) begin for(k6=0;k6<1;k6=k6+1) s6[k6] <= w6_0[k6]; end
assign sum_out={{8{s6[0][23]}},s6[0]}; endmodule
