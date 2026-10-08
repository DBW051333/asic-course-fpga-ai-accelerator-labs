// FC3: 32 个 56 位有符号乘积求和，完整结果为 61 位。
module fc3_adder_tree (
    input  wire [1791:0] data_i,
    output wire [60:0]   sum_o
);
    wire signed [55:0] level0 [0:31];
    wire signed [56:0] level1 [0:15];
    wire signed [57:0] level2 [0:7];
    wire signed [58:0] level3 [0:3];
    wire signed [59:0] level4 [0:1];
    wire signed [60:0] level5;

    genvar i;
    generate
        for (i = 0; i < 32; i = i + 1) begin : unpack
            assign level0[i] = data_i[1791-i*56 -: 56];
        end
        for (i = 0; i < 16; i = i + 1) begin : add1
            assign level1[i] = $signed(level0[2*i]) + $signed(level0[2*i+1]);
        end
        for (i = 0; i < 8; i = i + 1) begin : add2
            assign level2[i] = $signed(level1[2*i]) + $signed(level1[2*i+1]);
        end
        for (i = 0; i < 4; i = i + 1) begin : add3
            assign level3[i] = $signed(level2[2*i]) + $signed(level2[2*i+1]);
        end
        for (i = 0; i < 2; i = i + 1) begin : add4
            assign level4[i] = $signed(level3[2*i]) + $signed(level3[2*i+1]);
        end
    endgenerate

    assign level5 = $signed(level4[0]) + $signed(level4[1]);
    assign sum_o = level5;
endmodule
