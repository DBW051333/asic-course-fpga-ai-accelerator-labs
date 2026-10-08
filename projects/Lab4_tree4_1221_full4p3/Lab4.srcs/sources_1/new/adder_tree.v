`timescale 1ns / 1ps
// 64 signed 16-bit products, exact 22-bit group sum.
module adder_tree (
    input wire clk, input wire rst_n,
    input wire [1023:0] data,
    output wire [31:0] sum_out
);
wire signed [15:0] product [0:63];
genvar p;
generate for (p=0; p<64; p=p+1) begin: unpack
    assign product[p] = data[1023-p*16 -: 16];
end endgenerate
wire signed [16:0] level1 [0:31];
genvar g1;
generate for (g1=0; g1<32; g1=g1+1) begin: add1
    assign level1[g1] =
        {product[2*g1][15], product[2*g1]} +
        {product[2*g1+1][15], product[2*g1+1]};
end endgenerate
reg signed [16:0] stage1 [0:31];
integer i1;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i1=0; i1<32; i1=i1+1) stage1[i1] <= 17'sd0;
    end else begin
        for (i1=0; i1<32; i1=i1+1) stage1[i1] <= level1[i1];
    end
end
wire signed [17:0] level2 [0:15];
genvar g2;
generate for (g2=0; g2<16; g2=g2+1) begin: add2
    assign level2[g2] =
        {stage1[2*g2][16], stage1[2*g2]} +
        {stage1[2*g2+1][16], stage1[2*g2+1]};
end endgenerate
wire signed [18:0] level3 [0:7];
genvar g3;
generate for (g3=0; g3<8; g3=g3+1) begin: add3
    assign level3[g3] =
        {level2[2*g3][17], level2[2*g3]} +
        {level2[2*g3+1][17], level2[2*g3+1]};
end endgenerate
reg signed [18:0] stage2 [0:7];
integer i2;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i2=0; i2<8; i2=i2+1) stage2[i2] <= 19'sd0;
    end else begin
        for (i2=0; i2<8; i2=i2+1) stage2[i2] <= level3[i2];
    end
end
wire signed [19:0] level4 [0:3];
genvar g4;
generate for (g4=0; g4<4; g4=g4+1) begin: add4
    assign level4[g4] =
        {stage2[2*g4][18], stage2[2*g4]} +
        {stage2[2*g4+1][18], stage2[2*g4+1]};
end endgenerate
wire signed [20:0] level5 [0:1];
genvar g5;
generate for (g5=0; g5<2; g5=g5+1) begin: add5
    assign level5[g5] =
        {level4[2*g5][19], level4[2*g5]} +
        {level4[2*g5+1][19], level4[2*g5+1]};
end endgenerate
reg signed [20:0] stage3 [0:1];
integer i3;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i3=0; i3<2; i3=i3+1) stage3[i3] <= 21'sd0;
    end else begin
        for (i3=0; i3<2; i3=i3+1) stage3[i3] <= level5[i3];
    end
end
wire signed [21:0] level6 [0:0];
genvar g6;
generate for (g6=0; g6<1; g6=g6+1) begin: add6
    assign level6[g6] =
        {stage3[2*g6][20], stage3[2*g6]} +
        {stage3[2*g6+1][20], stage3[2*g6+1]};
end endgenerate
reg signed [21:0] stage4 [0:0];
integer i4;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i4=0; i4<1; i4=i4+1) stage4[i4] <= 22'sd0;
    end else begin
        for (i4=0; i4<1; i4=i4+1) stage4[i4] <= level6[i4];
    end
end
assign sum_out = {{10{stage4[0][21]}}, stage4[0]};
endmodule
