// Independent FC layer: input-stationary streaming, parallel output MACs.
// IW/AW are exact widths proven for all signed 8-bit inputs and fixed model weights.
module fc_stream_two_inputs #(
    parameter IW=23, NI=128, NO=32, AW=35, OW=48,
    parameter IA=7, OA=5, RELU=1,
    parameter WEIGHT_FILE="", BIAS_FILE=""
) (
    input wire clk_i, rst_n_i,
    input wire valid_i,
    input wire [IW-1:0] data_i, data_b_i, data_c_i, data_d_i,
    input wire [IA-1:0] addr_i,
    output reg valid_o,
    output reg [OW-1:0] data_o,
    output reg [OA-1:0] addr_o,
    output reg done_o
);
    localparam PW=IW+8;
    localparam ROM_STYLE=(NO==2)?"distributed":"block";
    (* rom_style=ROM_STYLE *) reg [NO*32-1:0] weights [0:NI-1];
    reg signed [7:0] biases [0:NO-1];
    initial begin
        $readmemh(WEIGHT_FILE, weights);
        $readmemh(BIAS_FILE, biases);
    end
    reg [NO*32-1:0] weight_r;
    reg signed [IW-1:0] data_r,data_d,data_b_r,data_b_d,data_c_r,data_c_d,data_d_r,data_d_d;
    reg [NO*32-1:0] weight_d;
    (* use_dsp="yes" *) reg signed [PW-1:0] product [0:NO*4-1];
    reg signed [PW-1:0] product_r [0:NO*4-1];
    reg signed [PW:0] sum_a [0:NO-1],sum_b [0:NO-1];
    reg signed [PW+1:0] sum_r [0:NO-1];
    reg signed [AW-1:0] acc [0:NO-1];
    reg [5:0] valid_pipe, first_pipe, last_pipe;
    reg emitting;
    reg [OA-1:0] emit_idx, read_addr;
    reg signed [AW-1:0] read_data;
    reg read_valid;
    integer j;
    always @(posedge clk_i) begin
        weight_r <= weights[addr_i];
        data_r <= data_i; data_b_r<=data_b_i;data_c_r<=data_c_i;data_d_r<=data_d_i;
        data_d <= data_r; data_b_d<=data_b_r;data_c_d<=data_c_r;data_d_d<=data_d_r; weight_d <= weight_r;
        for(j=0;j<NO;j=j+1) begin
            product[j*4] <= data_d * $signed(weight_d[NO*32-1-j*32 -:8]);
            product[j*4+1] <= data_b_d * $signed(weight_d[NO*32-9-j*32 -:8]);
            product[j*4+2] <= data_c_d * $signed(weight_d[NO*32-17-j*32 -:8]);
            product[j*4+3] <= data_d_d * $signed(weight_d[NO*32-25-j*32 -:8]);
            product_r[j*4]<=product[j*4];product_r[j*4+1]<=product[j*4+1];
            product_r[j*4+2]<=product[j*4+2];product_r[j*4+3]<=product[j*4+3];
            sum_a[j]<={product_r[j*4][PW-1],product_r[j*4]}+{product_r[j*4+1][PW-1],product_r[j*4+1]};
            sum_b[j]<={product_r[j*4+2][PW-1],product_r[j*4+2]}+{product_r[j*4+3][PW-1],product_r[j*4+3]};
            sum_r[j]<={sum_a[j][PW],sum_a[j]}+{sum_b[j][PW],sum_b[j]};
        end
        if(!rst_n_i) begin
            valid_pipe<=0; first_pipe<=0; last_pipe<=0;
            emitting<=0; emit_idx<=0; read_valid<=0;
            valid_o<=0; done_o<=0; addr_o<=0; data_o<=0;
        end else begin
            valid_pipe <= {valid_pipe[4:0],valid_i};
            first_pipe <= {first_pipe[4:0],addr_i==0};
            last_pipe <= {last_pipe[4:0],addr_i==NI-1};
            if(valid_pipe[5]) begin
                for(j=0;j<NO;j=j+1) begin
                    if(first_pipe[5])
                        acc[j] <= {{(AW-PW-2){sum_r[j][PW+1]}},sum_r[j]}
                                + {{(AW-8){biases[j][7]}},biases[j]};
                    else
                        acc[j] <= acc[j] + {{(AW-PW-2){sum_r[j][PW+1]}},sum_r[j]};
                end
                if(last_pipe[5]) begin emitting<=1; emit_idx<=0; end
            end
            read_valid<=emitting;
            if(emitting) begin
                read_data<=acc[emit_idx]; read_addr<=emit_idx;
                if(emit_idx==NO-1) emitting<=0;
                else emit_idx<=emit_idx+1'b1;
            end
            valid_o<=read_valid; addr_o<=read_addr;
            data_o <= (RELU && read_data[AW-1]) ? {OW{1'b0}}
                      : {{(OW-AW){read_data[AW-1]}},read_data};
            done_o <= read_valid && (read_addr==NO-1);
        end
    end
endmodule
