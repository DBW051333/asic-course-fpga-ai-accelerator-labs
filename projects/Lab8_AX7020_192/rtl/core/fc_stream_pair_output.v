`timescale 1ns/1ps
// Independent FC layer: input-stationary streaming, parallel output MACs.
// IW/AW are exact widths proven for all signed 8-bit inputs and fixed model weights.
module fc_stream_pair_output #(
    parameter IW=23, NI=128, NO=32, AW=35, OW=48,
    parameter IA=7, OA=5, RELU=1,
    parameter WEIGHT_FILE="", BIAS_FILE=""
) (
    input wire clk_i, rst_n_i, ce_i,
    input wire valid_i,
    input wire [IW-1:0] data_i,
    input wire [IA-1:0] addr_i,
    output reg valid_o,
    output reg [OW-1:0] data_o, data_b_o, data_c_o, data_d_o,
    output reg [OA-1:0] addr_o,
    output reg done_o
);
    localparam PW=IW+8;
    localparam RW=(NO/2)*25;
    localparam ROM_STYLE=(NO==2)?"distributed":"block";
    (* rom_style=ROM_STYLE *) reg [RW-1:0] weights [0:NI-1];
    reg signed [7:0] biases [0:NO-1];
    initial begin
        $readmemh(WEIGHT_FILE, weights);
        $readmemh(BIAS_FILE, biases);
    end
    reg [RW-1:0] weight_r;
    reg signed [IW-1:0] data_r,data_d;
    reg [RW-1:0] weight_d,weight_e;
    reg signed [IW-1:0] data_e;
    wire signed [PW-1:0] product [0:NO-1];
    reg signed [PW-1:0] product_r [0:NO-1];
    reg signed [AW-1:0] acc [0:NO-1], snapshot [0:NO-1];
    reg [4:0] valid_pipe, first_pipe, last_pipe;
    reg [2:0] emit_delay;
    reg emitting;
    reg [OA-1:0] emit_idx, read_addr;
    reg signed [AW-1:0] read_data, read_data_b,read_data_c,read_data_d;
    reg read_valid;

    localparam PPW=IW+25;
    genvar g;generate for(g=0;g<NO/2;g=g+1)begin:packed_mult
      wire signed [24:0] packed_w=weight_e[RW-1-g*25 -:25];
      (* use_dsp="yes" *) reg signed [PPW-1:0] packed_p;
      always @(posedge clk_i) if(ce_i)packed_p<=packed_w*data_e;
      wire signed [15:0] high_product=$signed(packed_p[PPW-1:16])+{15'd0,packed_p[15]};
      assign product[2*g]=packed_p[PW-1:0];
      assign product[2*g+1]=high_product[PW-1:0];
    end endgenerate
    genvar ch;generate for(ch=0;ch<NO;ch=ch+1)begin:single_acc
      wire signed [AW-1:0] prod={{(AW-PW){product_r[ch][PW-1]}},product_r[ch]};
      wire signed [AW-1:0] bias={{(AW-8){biases[ch][7]}},biases[ch]};
      wire signed [AW-1:0] base=first_pipe[4]?bias:acc[ch];
      wire signed [AW-1:0] next_sum=base+prod;
      always @(posedge clk_i) if(ce_i && valid_pipe[4])begin
        acc[ch]<=next_sum;
        // Capture before the next sample can overwrite the accumulator.
        if(last_pipe[4])snapshot[ch]<=next_sum;
      end
    end endgenerate
    integer j;
    always @(posedge clk_i) if(ce_i) begin
        weight_r <= weights[addr_i];
        data_r <= data_i;
        data_d <= data_r; weight_d <= weight_r;
        data_e <= data_d; weight_e <= weight_d;
        for(j=0;j<NO;j=j+1) begin
            product_r[j] <= product[j];
        end
    end
    always @(posedge clk_i) if(!rst_n_i || ce_i) begin
        if(!rst_n_i) begin
            valid_pipe<=0; first_pipe<=0; last_pipe<=0;emit_delay<=0;
            emitting<=0; emit_idx<=0; read_valid<=0;
            valid_o<=0; done_o<=0; addr_o<=0; data_o<=0;
        end else begin
            valid_pipe <= {valid_pipe[3:0],valid_i};
            first_pipe <= {first_pipe[3:0],addr_i==0};
            last_pipe <= {last_pipe[3:0],addr_i==NI-1};
            // Restore the former three-cycle accumulation/merge drain.
            // Outputs, feature writes and downstream FC3 remain cycle-identical.
            emit_delay<={emit_delay[1:0],valid_pipe[4] && last_pipe[4]};
            if(emit_delay[2])begin emitting<=1;emit_idx<=0;end
            read_valid<=emitting;
            if(emitting) begin
                read_data<=snapshot[emit_idx]; read_data_b<=snapshot[emit_idx+1'b1];read_data_c<=snapshot[emit_idx+2'd2];read_data_d<=snapshot[emit_idx+2'd3]; read_addr<=emit_idx;
                if(emit_idx==NO-4) emitting<=0;
                else emit_idx<=emit_idx+3'd4;
            end
            valid_o<=read_valid; addr_o<=read_addr;
            data_o <= (RELU && read_data[AW-1]) ? {OW{1'b0}}
                      : {{(OW-AW){read_data[AW-1]}},read_data};
            data_b_o <= (RELU && read_data_b[AW-1]) ? {OW{1'b0}} : {{(OW-AW){read_data_b[AW-1]}},read_data_b};
            data_c_o <= (RELU && read_data_c[AW-1]) ? {OW{1'b0}} : {{(OW-AW){read_data_c[AW-1]}},read_data_c};
            data_d_o <= (RELU && read_data_d[AW-1]) ? {OW{1'b0}} : {{(OW-AW){read_data_d[AW-1]}},read_data_d};
            done_o <= read_valid && (read_addr==NO-4);
        end
    end
endmodule
