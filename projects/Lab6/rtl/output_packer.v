// 将连续的标量全连接输出打包为一条宽 BRAM 写数据。
// Lab5 中使用 ELEM_WIDTH=32、ELEMENTS=32：FC1 的 128 个结果形成 4 条
// 1024 位数据，FC2 的 32 个结果形成 1 条 1024 位数据。
module output_packer #(
    parameter integer ELEM_WIDTH = 32,
    parameter integer ELEMENTS   = 32,
    parameter integer ADDR_WIDTH = 2
) (
    input  wire                              clk_i,
    input  wire                              rst_n_i,
    input  wire                              elem_valid_i,
    input  wire [ELEM_WIDTH-1:0]             elem_data_i,
    output reg                               vector_wren_o,
    output reg  [ELEM_WIDTH*ELEMENTS-1:0]    vector_data_o,
    output reg  [ADDR_WIDTH-1:0]             vector_addr_o
);

    localparam integer COUNT_WIDTH = (ELEMENTS > 1) ? $clog2(ELEMENTS) : 1;
    localparam [COUNT_WIDTH-1:0] LAST_ELEM = ELEMENTS - 1;
    reg [COUNT_WIDTH-1:0] elem_count;
    reg [ELEM_WIDTH*(ELEMENTS-1)-1:0] pending_data;
    reg [ADDR_WIDTH-1:0] write_addr;

    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            elem_count    <= {COUNT_WIDTH{1'b0}};
            pending_data  <= {ELEM_WIDTH*(ELEMENTS-1){1'b0}};
            vector_wren_o <= 1'b0;
            vector_data_o <= {ELEM_WIDTH*ELEMENTS{1'b0}};
            vector_addr_o <= {ADDR_WIDTH{1'b0}};
            write_addr    <= {ADDR_WIDTH{1'b0}};
        end else begin
            vector_wren_o <= 1'b0;
            if (elem_valid_i) begin
                if (elem_count == LAST_ELEM) begin
                    vector_data_o <= {pending_data, elem_data_i};
                    vector_wren_o <= 1'b1;
                    vector_addr_o <= write_addr;
                    write_addr    <= write_addr + 1'b1;
                    elem_count    <= {COUNT_WIDTH{1'b0}};
                    pending_data  <= {ELEM_WIDTH*(ELEMENTS-1){1'b0}};
                end else begin
                    pending_data <= {pending_data[ELEM_WIDTH*(ELEMENTS-1)-ELEM_WIDTH-1:0], elem_data_i};
                    elem_count   <= elem_count + 1'b1;
                end
            end
        end
    end
endmodule
