module cut_adder_tree #(
    parameter integer WIDTH = 8
)(
    input wire [32*(WIDTH+8)-1:0] data_i,
    output wire signed [WIDTH+12:0] sum_o
);
    wire signed [WIDTH+7:0] p [0:31];
    wire signed [WIDTH+8:0] l1 [0:15];
    wire signed [WIDTH+9:0] l2 [0:7];
    wire signed [WIDTH+10:0] l3 [0:3];
    wire signed [WIDTH+11:0] l4 [0:1];
    genvar i;
    generate
        for (i=0; i<32; i=i+1) begin: unpack
            assign p[i] = data_i[32*(WIDTH+8)-1-i*(WIDTH+8) -: (WIDTH+8)];
        end
        for (i=0; i<16; i=i+1) begin: add1
            assign l1[i] = $signed(p[2*i]) + $signed(p[2*i+1]);
        end
        for (i=0; i<8; i=i+1) begin: add2
            assign l2[i] = $signed(l1[2*i]) + $signed(l1[2*i+1]);
        end
        for (i=0; i<4; i=i+1) begin: add3
            assign l3[i] = $signed(l2[2*i]) + $signed(l2[2*i+1]);
        end
        for (i=0; i<2; i=i+1) begin: add4
            assign l4[i] = $signed(l3[2*i]) + $signed(l3[2*i+1]);
        end
    endgenerate
    assign sum_o = $signed(l4[0]) + $signed(l4[1]);
endmodule
