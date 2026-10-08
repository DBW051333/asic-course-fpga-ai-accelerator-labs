// Lab5 顶层：Lab4 FC1 -> 独立 FC2 -> 独立 FC3。
module lab5_top (
    input  wire        clk_i,
    input  wire        rst_n_i,
    input  wire        start_i,
    output wire        done_o,
    output wire        fc1_wren_o,
    output wire [31:0] fc1_data_o,
    output wire [6:0]  fc1_addr_o,
    output wire        fc2_wren_o,
    output wire [47:0] fc2_data_o,
    output wire [4:0]  fc2_addr_o,
    output wire        fc3_wren_o,
    output wire [63:0] fc3_data_o,
    output wire        fc3_addr_o
);
    wire fc1_start;
    wire fc2_start;
    wire fc3_start;
    wire fc1_done;
    wire fc2_done;
    wire fc3_done;

    lab5_controller u_controller (
        .clk_i(clk_i), .rst_n_i(rst_n_i), .start_i(start_i),
        .fc1_done_i(fc1_done), .fc2_done_i(fc2_done), .fc3_done_i(fc3_done),
        .fc1_start_o(fc1_start), .fc2_start_o(fc2_start), .fc3_start_o(fc3_start),
        .done_o(done_o)
    );

    // FC1 完整沿用 Lab4 已验证模块，输出为 128 个 32 位结果。
    fc_top u_fc1 (
        .clk_i(clk_i), .rst_n_i(rst_n_i), .start_i(fc1_start), .done_o(fc1_done),
        .fc_output_wren_o(fc1_wren_o), .fc_output_data_o(fc1_data_o),
        .fc_output_addr_o(fc1_addr_o)
    );

    // 每 32 个 FC1 输出打成一行，形成 FC2 的 4 行输入 RAM。
    wire          fc1_pack_wren;
    wire [1023:0] fc1_pack_data;
    wire [1:0]    fc1_pack_addr;
    output_packer #(.ELEM_WIDTH(32), .ELEMENTS(32), .ADDR_WIDTH(2)) u_fc1_packer (
        .clk_i(clk_i), .rst_n_i(rst_n_i),
        .elem_valid_i(fc1_wren_o), .elem_data_i(fc1_data_o),
        .vector_wren_o(fc1_pack_wren), .vector_data_o(fc1_pack_data),
        .vector_addr_o(fc1_pack_addr)
    );

    wire [1:0]    fc2_input_addr;
    wire [1023:0] fc2_input_data;
    wire [6:0]    fc2_weight_addr;
    wire [255:0]  fc2_weight_data;
    wire [4:0]    fc2_bias_addr;
    wire [7:0]    fc2_bias_data;
    wire [1023:0] fc2_mul_data1;
    wire [255:0]  fc2_mul_data2;
    wire [1279:0] fc2_mul_result;

    fc2_input_ram u_fc2_input_ram (
        .clka(clk_i), .wea(fc1_pack_wren),
        .addra(fc1_pack_wren ? fc1_pack_addr : fc2_input_addr),
        .dina(fc1_pack_data), .douta(fc2_input_data)
    );
    fc2_weight_ram u_fc2_weight_ram (
        .clka(clk_i), .wea(1'b0), .addra(fc2_weight_addr),
        .dina(256'd0), .douta(fc2_weight_data)
    );
    fc2_bias_ram u_fc2_bias_ram (
        .clka(clk_i), .wea(1'b0), .addra(fc2_bias_addr),
        .dina(8'd0), .douta(fc2_bias_data)
    );
    fc2_mult_array u_fc2_mult_array (
        .clk_i(clk_i), .rst_n_i(rst_n_i),
        .data_i(fc2_mul_data1), .weight_i(fc2_mul_data2),
        .result_o(fc2_mul_result)
    );
    fc2 u_fc2 (
        .clk_i(clk_i), .rst_n_i(rst_n_i), .start_i(fc2_start), .done_o(fc2_done),
        .input_data_addr_o(fc2_input_addr), .input_data_i(fc2_input_data),
        .weight_addr_o(fc2_weight_addr), .weight_i(fc2_weight_data),
        .bias_addr_o(fc2_bias_addr), .bias_i(fc2_bias_data),
        .fc_output_wren_o(fc2_wren_o), .fc_output_data_o(fc2_data_o),
        .fc_output_addr_o(fc2_addr_o),
        .mul_data1_o(fc2_mul_data1), .mul_data2_o(fc2_mul_data2),
        .mul_result_i(fc2_mul_result)
    );
    fc2_output_ram u_fc2_output_ram (
        .clka(clk_i), .wea(fc2_wren_o), .addra(fc2_addr_o),
        .dina(fc2_data_o), .douta()
    );

    // FC2 的 32 个 48 位结果全部打包，作为 FC3 的一行输入。
    wire          fc2_pack_wren;
    wire [1535:0] fc2_pack_data;
    wire          fc2_pack_addr_unused;
    output_packer #(.ELEM_WIDTH(48), .ELEMENTS(32), .ADDR_WIDTH(1)) u_fc2_packer (
        .clk_i(clk_i), .rst_n_i(rst_n_i),
        .elem_valid_i(fc2_wren_o), .elem_data_i(fc2_data_o),
        .vector_wren_o(fc2_pack_wren), .vector_data_o(fc2_pack_data),
        .vector_addr_o(fc2_pack_addr_unused)
    );

    wire          fc3_input_addr;
    wire [1535:0] fc3_input_data;
    wire          fc3_weight_addr;
    wire [255:0]  fc3_weight_data;
    wire          fc3_bias_addr;
    wire [7:0]    fc3_bias_data;
    wire [1535:0] fc3_mul_data1;
    wire [255:0]  fc3_mul_data2;
    wire [1791:0] fc3_mul_result;

    fc3_input_ram u_fc3_input_ram (
        .clka(clk_i), .wea(fc2_pack_wren),
        .addra(fc2_pack_wren ? 1'b0 : fc3_input_addr),
        .dina(fc2_pack_data), .douta(fc3_input_data)
    );
    fc3_weight_ram u_fc3_weight_ram (
        .clka(clk_i), .wea(1'b0), .addra(fc3_weight_addr),
        .dina(256'd0), .douta(fc3_weight_data)
    );
    fc3_bias_ram u_fc3_bias_ram (
        .clka(clk_i), .wea(1'b0), .addra(fc3_bias_addr),
        .dina(8'd0), .douta(fc3_bias_data)
    );
    fc3_mult_array u_fc3_mult_array (
        .clk_i(clk_i), .rst_n_i(rst_n_i),
        .data_i(fc3_mul_data1), .weight_i(fc3_mul_data2),
        .result_o(fc3_mul_result)
    );
    fc3 u_fc3 (
        .clk_i(clk_i), .rst_n_i(rst_n_i), .start_i(fc3_start), .done_o(fc3_done),
        .input_data_addr_o(fc3_input_addr), .input_data_i(fc3_input_data),
        .weight_addr_o(fc3_weight_addr), .weight_i(fc3_weight_data),
        .bias_addr_o(fc3_bias_addr), .bias_i(fc3_bias_data),
        .fc_output_wren_o(fc3_wren_o), .fc_output_data_o(fc3_data_o),
        .fc_output_addr_o(fc3_addr_o),
        .mul_data1_o(fc3_mul_data1), .mul_data2_o(fc3_mul_data2),
        .mul_result_i(fc3_mul_result)
    );
    fc3_output_ram u_fc3_output_ram (
        .clka(clk_i), .wea(fc3_wren_o), .addra(fc3_addr_o),
        .dina(fc3_data_o), .douta()
    );
endmodule
