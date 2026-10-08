// FC3 专用乘法器阵列：32 路 48 位输入乘 8 位权重。
module fc3_mult_array (
    input  wire          clk_i,
    input  wire          rst_n_i,
    input  wire [1535:0] data_i,
    input  wire [255:0]  weight_i,
    output wire [1791:0] result_o
);
    genvar i;
    generate
        for (i = 0; i < 32; i = i + 1) begin : gen_mult
            fc3_mult_48x8 u_mult (
                .CLK  (clk_i),
                .A    (data_i[1535-i*48 -: 48]),
                .B    (weight_i[255-i*8 -: 8]),
                .SCLR (~rst_n_i),
                .P    (result_o[1791-i*56 -: 56])
            );
        end
    endgenerate
endmodule
