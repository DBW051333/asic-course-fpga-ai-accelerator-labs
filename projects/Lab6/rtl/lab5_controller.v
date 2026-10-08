// 三层串行调度：FC1 完成后启动 FC2，FC2 完成后启动 FC3。
// 每一层完成后保留两个时钟周期，确保最后一笔输出 RAM 写入对下一层可见。
module lab5_controller (
    input  wire clk_i,
    input  wire rst_n_i,
    input  wire start_i,
    input  wire fc1_done_i,
    input  wire fc2_done_i,
    input  wire fc3_done_i,
    output reg  fc1_start_o,
    output reg  fc2_start_o,
    output reg  fc3_start_o,
    output reg  done_o
);
    localparam [3:0] IDLE = 4'd0, FC1 = 4'd1, GAP1 = 4'd2,
                     FC2 = 4'd3, GAP2 = 4'd4, FC3 = 4'd5;
    reg [3:0] state;
    reg gap_phase;

    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            state       <= IDLE;
            gap_phase   <= 1'b0;
            fc1_start_o <= 1'b0;
            fc2_start_o <= 1'b0;
            fc3_start_o <= 1'b0;
            done_o      <= 1'b0;
        end else begin
            fc1_start_o <= 1'b0;
            fc2_start_o <= 1'b0;
            fc3_start_o <= 1'b0;
            done_o      <= 1'b0;
            case (state)
                IDLE: if (start_i) begin
                    fc1_start_o <= 1'b1;
                    state       <= FC1;
                end
                FC1: if (fc1_done_i) begin gap_phase <= 1'b0; state <= GAP1; end
                GAP1: if (gap_phase) begin fc2_start_o <= 1'b1; state <= FC2; end
                      else gap_phase <= 1'b1;
                FC2: if (fc2_done_i) begin gap_phase <= 1'b0; state <= GAP2; end
                GAP2: if (gap_phase) begin fc3_start_o <= 1'b1; state <= FC3; end
                      else gap_phase <= 1'b1;
                FC3: if (fc3_done_i) begin done_o <= 1'b1; state <= IDLE; end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
