// 第二层全连接：128 输入、32 输出、ReLU。
// 每次并行计算 32 个乘法，4 组完成一个输出；结果保留 48 位。
module fc2 (
    input  wire          clk_i,
    input  wire          rst_n_i,
    input  wire          start_i,
    output reg           done_o,

    output reg  [1:0]    input_data_addr_o,
    input  wire [1023:0] input_data_i,
    output reg  [6:0]    weight_addr_o,
    input  wire [255:0]  weight_i,
    output reg  [4:0]    bias_addr_o,
    input  wire [7:0]    bias_i,

    output reg           fc_output_wren_o,
    output reg  [47:0]   fc_output_data_o,
    output reg  [4:0]    fc_output_addr_o,

    output wire [1023:0] mul_data1_o,
    output wire [255:0]  mul_data2_o,
    input  wire [1279:0] mul_result_i
);
    localparam [1:0] IDLE = 2'd0, ISSUE = 2'd1, WAIT_RESULT = 2'd2, ACCUM = 2'd3;
    localparam [3:0] RESULT_WAIT_CYCLES = 4'd7;

    reg [1:0] state;
    reg [1:0] group_idx;
    reg [4:0] out_channel;
    reg [3:0] wait_count;
    reg signed [47:0] accumulator;

    wire signed [44:0] group_sum;
    wire signed [47:0] group_sum_ext = {{3{group_sum[44]}}, group_sum};
    wire signed [47:0] bias_ext = {{40{bias_i[7]}}, bias_i};
    wire signed [47:0] final_sum = accumulator + group_sum_ext + bias_ext;

    assign mul_data1_o = input_data_i;
    assign mul_data2_o = weight_i;

    fc2_adder_tree u_adder_tree (
        .data_i(mul_result_i),
        .sum_o(group_sum)
    );

    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            state                <= IDLE;
            group_idx            <= 2'd0;
            out_channel          <= 5'd0;
            wait_count           <= 4'd0;
            accumulator          <= 48'd0;
            input_data_addr_o    <= 2'd0;
            weight_addr_o        <= 7'd0;
            bias_addr_o          <= 5'd0;
            fc_output_wren_o     <= 1'b0;
            fc_output_data_o     <= 48'd0;
            fc_output_addr_o     <= 5'd0;
            done_o               <= 1'b0;
        end else begin
            fc_output_wren_o <= 1'b0;
            done_o           <= 1'b0;
            case (state)
                IDLE: begin
                    if (start_i) begin
                        group_idx   <= 2'd0;
                        out_channel <= 5'd0;
                        accumulator <= 48'd0;
                        state       <= ISSUE;
                    end
                end
                ISSUE: begin
                    input_data_addr_o <= group_idx;
                    weight_addr_o     <= {out_channel, 2'b00} + group_idx;
                    bias_addr_o       <= out_channel;
                    wait_count        <= 4'd0;
                    state             <= WAIT_RESULT;
                end
                WAIT_RESULT: begin
                    if (wait_count == RESULT_WAIT_CYCLES)
                        state <= ACCUM;
                    else
                        wait_count <= wait_count + 1'b1;
                end
                ACCUM: begin
                    if (group_idx == 2'd3) begin
                        fc_output_wren_o <= 1'b1;
                        fc_output_addr_o <= out_channel;
                        fc_output_data_o <= final_sum[47] ? 48'd0 : final_sum;
                        accumulator      <= 48'd0;
                        group_idx        <= 2'd0;
                        if (out_channel == 5'd31) begin
                            done_o <= 1'b1;
                            state  <= IDLE;
                        end else begin
                            out_channel <= out_channel + 1'b1;
                            state       <= ISSUE;
                        end
                    end else begin
                        accumulator <= accumulator + group_sum_ext;
                        group_idx   <= group_idx + 1'b1;
                        state       <= ISSUE;
                    end
                end
            endcase
        end
    end
endmodule
