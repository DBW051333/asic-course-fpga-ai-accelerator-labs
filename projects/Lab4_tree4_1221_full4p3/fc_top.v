// Lab4 顶层：只负责连接 fc、4 个 BRAM IP 与乘法器阵列。
//
// 使用前请在 Vivado 中将四个 Block Memory Generator 的组件名设为：
//   fc_input_ram, fc_weight_ram, fc_bias_ram, fc_output_ram
// 本工程生成的 IP 不含 ena；输入 RAM 与偏置 RAM 额外含 rsta。
module fc_top (
    input  wire        clk_i,
    input  wire        rst_n_i,
    input  wire        start_i,
    output wire        done_o,

    // 暴露这些信号，便于 testbench 观察或将来连接下一层网络。
    output wire        fc_output_wren_o,
    output wire [31:0] fc_output_data_o,
    output wire [6:0]  fc_output_addr_o
);

    // fc 与输入 RAM 的连接线
    wire [2:0]    input_data_addr;
    wire [511:0] input_data;

    // fc 与权重 RAM 的连接线
    wire [9:0]    weight_addr;
    wire [511:0] weight_data;

    // fc 与偏置 RAM 的连接线
    wire [6:0] bias_addr;
    wire [7:0] bias_data;

    // fc 与乘法器阵列的连接线
    wire [511:0] mul_data1;
    wire [511:0] mul_data2;
    wire [1023:0] mul_result;

    // 输出 RAM 的 douta 在本实验中不用，可在仿真时需要读取 RAM 时使用。
    wire [31:0] output_ram_dout;

    fc u_fc (
        .clk_i             (clk_i),
        .rst_n_i           (rst_n_i),
        .start_i           (start_i),
        .done_o            (done_o),

        .input_data_addr_o (input_data_addr),
        .input_data_i      (input_data),

        .weight_addr_o     (weight_addr),
        .weight_i          (weight_data),

        .bias_addr_o       (bias_addr),
        .bias_i            (bias_data),

        .fc_output_wren_o  (fc_output_wren_o),
        .fc_output_data_o  (fc_output_data_o),
        .fc_output_addr_o  (fc_output_addr_o),

        .mul_data1_o       (mul_data1),
        .mul_data2_o       (mul_data2),
        .mul_result_i      (mul_result)
    );

    // COE：sel_data_64.coe，宽 512，深 8。
    fc_input_ram u_input_ram (
        .clka  (clk_i),
        .rsta  (~rst_n_i),
        .wea   (1'b0),
        .addra (input_data_addr),
        .dina  (512'd0),
        .douta (input_data)
    );

    // COE：fc1.0.weight_64.coe，宽 512，深 1024。
    fc_weight_ram u_weight_ram (
        .clka  (clk_i),
        .wea   (1'b0),
        .addra (weight_addr),
        .dina  (512'd0),
        .douta (weight_data)
    );

    // COE：模型参数/fc1.0.bias.coe，宽 8，深 128。
    fc_bias_ram u_bias_ram (
        .clka  (clk_i),
        .rsta  (~rst_n_i),
        .wea   (1'b0),
        .addra (bias_addr),
        .dina  (8'd0),
        .douta (bias_data)
    );

    // 输出 RAM：宽 32，深 128；fc 给出地址、数据与写使能。
    fc_output_ram u_output_ram (
        .clka  (clk_i),
        .wea   (fc_output_wren_o),
        .addra (fc_output_addr_o),
        .dina  (fc_output_data_o),
        .douta (output_ram_dout)
    );

    mult_array u_mult_array (
        .clk_i    (clk_i),
        .rst_n_i  (rst_n_i),
        .data1_i  (mul_data1),
        .data2_i  (mul_data2),
        .result_o (mul_result)
    );

endmodule
