`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 09/25/2026 01:21:10 PM
// Design Name: 
// Module Name: adder_tree
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module adder_tree (
    input  wire          clk,
    input  wire          rst_n,
    input  wire [2047:0] data,
    output wire [31:0]   sum_out
);

    genvar g;

    // 将 2048 位乘法结果拆成 128 个 16 位有符号乘积
    wire signed [15:0] product [0:127];

    generate
        for (g = 0; g < 128; g = g + 1) begin : gen_product
            assign product[g] = data[2047 - g*16 -: 16];
        end
    endgenerate

    // ---------- 流水线第 1 级：128 -> 32 ----------
    wire signed [16:0] level1 [0:63];
    wire signed [17:0] level2 [0:31];
    reg  signed [17:0] stage1 [0:31];

    generate
        for (g = 0; g < 64; g = g + 1) begin : gen_level1
            assign level1[g] =
                {product[2*g][15], product[2*g]} +
                {product[2*g+1][15], product[2*g+1]};
        end

        for (g = 0; g < 32; g = g + 1) begin : gen_level2
            assign level2[g] =
                {level1[2*g][16], level1[2*g]} +
                {level1[2*g+1][16], level1[2*g+1]};
        end
    endgenerate

    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1)
                stage1[i] <= 18'sd0;
        end else begin
            for (i = 0; i < 32; i = i + 1)
                stage1[i] <= level2[i];
        end
    end

    // ---------- 流水线第 2 级：32 -> 8 ----------
    wire signed [18:0] level3 [0:15];
    wire signed [19:0] level4 [0:7];
    reg  signed [19:0] stage2a [0:7];

    generate
        for (g = 0; g < 16; g = g + 1) begin : gen_level3
            assign level3[g] =
                {stage1[2*g][17], stage1[2*g]} +
                {stage1[2*g+1][17], stage1[2*g+1]};
        end

        for (g = 0; g < 8; g = g + 1) begin : gen_level4
            assign level4[g] =
                {level3[2*g][18], level3[2*g]} +
                {level3[2*g+1][18], level3[2*g+1]};
        end
    endgenerate

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 8; i = i + 1)
                stage2a[i] <= 20'sd0;
        end else begin
            for (i = 0; i < 8; i = i + 1)
                stage2a[i] <= level4[i];
        end
    end

    // ---------- 流水线第 3 级：8 -> 4 ----------
    wire signed [20:0] level5 [0:3];
    reg  signed [20:0] stage2 [0:3];

    generate
        for (g = 0; g < 4; g = g + 1) begin : gen_level5
            assign level5[g] =
                {stage2a[2*g][19], stage2a[2*g]} +
                {stage2a[2*g+1][19], stage2a[2*g+1]};
        end
    endgenerate

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 4; i = i + 1)
                stage2[i] <= 21'sd0;
        end else begin
            for (i = 0; i < 4; i = i + 1)
                stage2[i] <= level5[i];
        end
    end

    // ---------- 流水线第 4 级：4 -> 1 ----------
    wire signed [21:0] level6 [0:1];
    wire signed [22:0] level7;
    reg  signed [22:0] stage3;

    generate
        for (g = 0; g < 2; g = g + 1) begin : gen_level6
            assign level6[g] =
                {stage2[2*g][20], stage2[2*g]} +
                {stage2[2*g+1][20], stage2[2*g+1]};
        end
    endgenerate

    assign level7 =
        {level6[0][21], level6[0]} +
        {level6[1][21], level6[1]};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            stage3 <= 23'sd0;
        else
            stage3 <= level7;
    end

    // 符号扩展到 fc.v 所需的 32 位
    assign sum_out = {{9{stage3[22]}}, stage3};

endmodule
