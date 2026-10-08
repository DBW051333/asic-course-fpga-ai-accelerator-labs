// FC2/FC3 datapath: complete the MAC and bias addition before selecting bits.
module cut_fc_layer #(
    parameter integer WIDTH = 8,
    parameter integer GROUPS = 4,
    parameter integer OUTPUTS = 32,
    parameter integer SHIFT = 9,
    parameter integer RELU = 1
)(
    input wire clk_i, rst_n_i, start_i,
    output reg done_o,
    output reg [1:0] input_data_addr_o,
    input wire [32*WIDTH-1:0] input_data_i,
    output reg [6:0] weight_addr_o,
    input wire [255:0] weight_i,
    output reg [4:0] bias_addr_o,
    input wire [7:0] bias_i,
    output reg fc_output_wren_o,
    output reg [WIDTH-1:0] fc_output_data_o,
    output reg [4:0] fc_output_addr_o,
    output wire [32*WIDTH-1:0] mul_data1_o,
    output wire [255:0] mul_data2_o,
    input wire [32*(WIDTH+8)-1:0] mul_result_i
);
    localparam integer ACC_WIDTH = WIDTH + 16;
    localparam [1:0] IDLE=0, ISSUE=1, WAIT_RESULT=2, ACCUM=3;
    localparam [3:0] RESULT_WAIT_CYCLES = 7;
    reg [1:0] state;
    reg [1:0] group_idx;
    reg [4:0] out_channel;
    reg [3:0] wait_count;
    reg signed [ACC_WIDTH-1:0] accumulator;
    wire signed [WIDTH+12:0] group_sum;
    wire signed [ACC_WIDTH-1:0] group_ext = group_sum;
    wire signed [ACC_WIDTH-1:0] bias_ext = $signed(bias_i);
    wire signed [ACC_WIDTH-1:0] final_sum = accumulator + group_ext + bias_ext;
    wire signed [ACC_WIDTH-1:0] activated = (RELU && final_sum < 0) ? {ACC_WIDTH{1'b0}} : final_sum;

    assign mul_data1_o = input_data_i;
    assign mul_data2_o = weight_i;
    cut_adder_tree #(.WIDTH(WIDTH)) u_adder_tree (.data_i(mul_result_i), .sum_o(group_sum));

    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            state <= IDLE;
            group_idx <= 0;
            out_channel <= 0;
            wait_count <= 0;
            accumulator <= 0;
            input_data_addr_o <= 0;
            weight_addr_o <= 0;
            bias_addr_o <= 0;
            fc_output_wren_o <= 0;
            fc_output_data_o <= 0;
            fc_output_addr_o <= 0;
            done_o <= 0;
        end else begin
            fc_output_wren_o <= 0;
            done_o <= 0;
            case (state)
                IDLE: if (start_i) begin
                    group_idx <= 0;
                    out_channel <= 0;
                    accumulator <= 0;
                    state <= ISSUE;
                end
                ISSUE: begin
                    input_data_addr_o <= group_idx;
                    weight_addr_o <= out_channel * GROUPS + group_idx;
                    bias_addr_o <= out_channel;
                    wait_count <= 0;
                    state <= WAIT_RESULT;
                end
                WAIT_RESULT: begin
                    if (wait_count == RESULT_WAIT_CYCLES) state <= ACCUM;
                    else wait_count <= wait_count + 1'b1;
                end
                ACCUM: begin
                    if (group_idx == GROUPS-1) begin
                        fc_output_wren_o <= 1;
                        fc_output_addr_o <= out_channel;
                        fc_output_data_o <= activated[SHIFT +: WIDTH];
                        accumulator <= 0;
                        group_idx <= 0;
                        if (out_channel == OUTPUTS-1) begin
                            done_o <= 1;
                            state <= IDLE;
                        end else begin
                            out_channel <= out_channel + 1'b1;
                            state <= ISSUE;
                        end
                    end else begin
                        accumulator <= accumulator + group_ext;
                        group_idx <= group_idx + 1'b1;
                        state <= ISSUE;
                    end
                end
            endcase
        end
    end
endmodule
