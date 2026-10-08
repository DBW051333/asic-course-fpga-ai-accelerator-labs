// 32 signed WIDTH x 8 multipliers, retaining the Lab5 three-cycle IP pipeline.
module cut_mult_array #(
    parameter integer WIDTH = 8
)(
    input wire clk_i, rst_n_i,
    input wire [32*WIDTH-1:0] data_i,
    input wire [255:0] weight_i,
    output wire [32*(WIDTH+8)-1:0] result_o
);
    genvar i;
    generate for (i=0; i<32; i=i+1) begin: gen_mult
        cut_mult u_mult (
            .CLK(clk_i),
            .A(data_i[32*WIDTH-1-i*WIDTH -: WIDTH]),
            .B(weight_i[255-i*8 -: 8]),
            .SCLR(~rst_n_i),
            .P(result_o[32*(WIDTH+8)-1-i*(WIDTH+8) -: (WIDTH+8)])
        );
    end endgenerate
endmodule
