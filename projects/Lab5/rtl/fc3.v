// 第三层全连接：32 输入、2 输出、无激活函数；结果保留 64 位。
module fc3 (
    input  wire          clk_i,
    input  wire          rst_n_i,
    input  wire          start_i,
    output reg           done_o,

    output reg           input_data_addr_o,
    input  wire [1535:0] input_data_i,
    output reg           weight_addr_o,
    input  wire [255:0]  weight_i,
    output reg           bias_addr_o,
    input  wire [7:0]    bias_i,

    output reg           fc_output_wren_o,
    output reg  [63:0]   fc_output_data_o,
    output reg           fc_output_addr_o,

    output wire [1535:0] mul_data1_o,
    output wire [255:0]  mul_data2_o,
    input  wire [1791:0] mul_result_i
);
    localparam [1:0] IDLE = 2'd0, ISSUE = 2'd1, WAIT_RESULT = 2'd2, WRITE_RESULT = 2'd3;
    localparam [3:0] RESULT_WAIT_CYCLES = 4'd7;

    reg [1:0] state;
    reg out_channel;
    reg [3:0] wait_count;

    wire signed [60:0] group_sum;
    wire signed [63:0] group_sum_ext = {{3{group_sum[60]}}, group_sum};
    wire signed [63:0] bias_ext = {{56{bias_i[7]}}, bias_i};
    wire signed [63:0] final_sum = group_sum_ext + bias_ext;

    assign mul_data1_o = input_data_i;
    assign mul_data2_o = weight_i;

    fc3_adder_tree u_adder_tree (
        .data_i(mul_result_i),
        .sum_o(group_sum)
    );

    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            state                <= IDLE;
            out_channel          <= 1'b0;
            wait_count           <= 4'd0;
            input_data_addr_o    <= 1'b0;
            weight_addr_o        <= 1'b0;
            bias_addr_o          <= 1'b0;
            fc_output_wren_o     <= 1'b0;
            fc_output_data_o     <= 64'd0;
            fc_output_addr_o     <= 1'b0;
            done_o               <= 1'b0;
        end else begin
            fc_output_wren_o <= 1'b0;
            done_o           <= 1'b0;
            case (state)
                IDLE: begin
                    if (start_i) begin
                        out_channel <= 1'b0;
                        state       <= ISSUE;
                    end
                end
                ISSUE: begin
                    input_data_addr_o <= 1'b0;
                    weight_addr_o     <= out_channel;
                    bias_addr_o       <= out_channel;
                    wait_count        <= 4'd0;
                    state             <= WAIT_RESULT;
                end
                WAIT_RESULT: begin
                    if (wait_count == RESULT_WAIT_CYCLES)
                        state <= WRITE_RESULT;
                    else
                        wait_count <= wait_count + 1'b1;
                end
                WRITE_RESULT: begin
                    fc_output_wren_o <= 1'b1;
                    fc_output_data_o <= final_sum;
                    fc_output_addr_o <= out_channel;
                    if (out_channel) begin
                        done_o <= 1'b1;
                        state  <= IDLE;
                    end else begin
                        out_channel <= 1'b1;
                        state       <= ISSUE;
                    end
                end
            endcase
        end
    end
endmodule
