// 128 路 8 位乘法器阵列。
module mult_array (
    input  wire          clk_i,
    input  wire          rst_n_i,
    input  wire [1023:0] data1_i,
    input  wire [1023:0] data2_i,
    output wire [2047:0] result_o
);

    genvar i;
    generate
        for (i = 0; i < 128; i = i + 1) begin : gen_mult
            mult_8 u_mult_8 (
                .CLK  (clk_i),
                .A    (data1_i[1023 - i*8 -: 8]),
                .B    (data2_i[1023 - i*8 -: 8]),
                .SCLR (~rst_n_i),
                .P    (result_o[2047 - i*16 -: 16])
            );
        end
    endgenerate

endmodule
