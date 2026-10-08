// FC2 专用乘法器阵列：32 路 32 位输入乘 8 位权重。
module fc2_mult_array (
    input  wire          clk_i,
    input  wire          rst_n_i,
    input  wire [1023:0] data_i,
    input  wire [255:0]  weight_i,
    output wire [1279:0] result_o
);
    genvar i;
    generate
        for (i = 0; i < 32; i = i + 1) begin : gen_mult
            fc2_mult_32x8 u_mult (
                .CLK  (clk_i),
                .A    (data_i[1023-i*32 -: 32]),
                .B    (weight_i[255-i*8 -: 8]),
                .SCLR (~rst_n_i),
                .P    (result_o[1279-i*40 -: 40])
            );
        end
    endgenerate
endmodule
