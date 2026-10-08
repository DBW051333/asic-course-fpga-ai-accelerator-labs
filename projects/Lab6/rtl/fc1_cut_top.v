// Reuse the verified Lab5 FC1 datapath. Cut only after bias and ReLU.
module fc1_cut_top #(
    parameter integer OUT_WIDTH = 8,
    parameter integer SHIFT = 10
)(
    input wire clk_i, rst_n_i, start_i,
    input wire input_we_i,
    input wire [1:0] input_addr_i,
    input wire [1023:0] input_data_i,
    output wire done_o, fc_output_wren_o,
    output wire [OUT_WIDTH-1:0] fc_output_data_o,
    output wire [6:0] fc_output_addr_o
);
    wire [1:0] input_addr;
    wire [1023:0] input_data, weight_data, mul_data1, mul_data2;
    wire [8:0] weight_addr;
    wire [6:0] bias_addr;
    wire [7:0] bias_data;
    wire [2047:0] mul_result;
    wire [31:0] full_output;

    fc u_fc (
        .clk_i(clk_i), .rst_n_i(rst_n_i), .start_i(start_i), .done_o(done_o),
        .input_data_addr_o(input_addr), .input_data_i(input_data),
        .weight_addr_o(weight_addr), .weight_i(weight_data),
        .bias_addr_o(bias_addr), .bias_i(bias_data),
        .fc_output_wren_o(fc_output_wren_o), .fc_output_data_o(full_output),
        .fc_output_addr_o(fc_output_addr_o),
        .mul_data1_o(mul_data1), .mul_data2_o(mul_data2), .mul_result_i(mul_result)
    );
    assign fc_output_data_o = full_output[SHIFT +: OUT_WIDTH];
    fc_input_ram u_input_ram (
        .clka(clk_i), .rsta(~rst_n_i), .wea(input_we_i),
        .addra(input_we_i ? input_addr_i : input_addr),
        .dina(input_data_i), .douta(input_data)
    );
    fc_weight_ram u_weight_ram (
        .clka(clk_i), .wea(1'b0), .addra(weight_addr),
        .dina(1024'd0), .douta(weight_data)
    );
    fc_bias_ram u_bias_ram (
        .clka(clk_i), .rsta(~rst_n_i), .wea(1'b0), .addra(bias_addr),
        .dina(8'd0), .douta(bias_data)
    );
    fc_output_ram u_output_ram (
        .clka(clk_i), .wea(fc_output_wren_o), .addra(fc_output_addr_o),
        .dina(fc_output_data_o), .douta()
    );
    mult_array u_mult_array (
        .clk_i(clk_i), .rst_n_i(rst_n_i),
        .data1_i(mul_data1), .data2_i(mul_data2), .result_o(mul_result)
    );
endmodule
