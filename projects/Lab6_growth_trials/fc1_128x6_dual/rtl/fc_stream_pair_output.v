// Independent FC layer: input-stationary streaming, parallel output MACs.
// IW/AW are exact widths proven for all signed 8-bit inputs and fixed model weights.
module fc_stream_pair_output #(
    parameter IW=23, NI=128, NO=32, AW=35, OW=48,
    parameter IA=7, OA=5, RELU=1,
    parameter WEIGHT_FILE="", BIAS_FILE=""
) (
    input wire clk_i, rst_n_i,
    input wire valid_i,
    input wire [IW-1:0] data_i,data_b_i,
    input wire [IA-1:0] addr_i,
    output reg valid_o,
    output reg [OW-1:0] data_o, data_b_o, data_c_o, data_d_o,
    output reg [OA-1:0] addr_o,
    output reg done_o
);
    localparam PW=IW+9;
    localparam RW=NO*25;
    localparam ROM_STYLE=(NO==2)?"distributed":"block";
    (* rom_style=ROM_STYLE *) reg [RW-1:0] weights [0:NI-1];
    reg signed [7:0] biases [0:NO-1];
    initial begin
        $readmemh(WEIGHT_FILE, weights);
        $readmemh(BIAS_FILE, biases);
    end
    reg [RW-1:0] weight_r;
    reg signed [IW-1:0] data_r,data_d,data_b_r,data_b_d;
    reg [RW-1:0] weight_d,weight_e;
    reg signed [IW-1:0] data_e,data_b_e;
    wire signed [PW-1:0] product [0:NO-1];
    reg signed [PW-1:0] product_r [0:NO-1];
    reg signed [AW-1:0] acc [0:NO-1], snapshot [0:NO-1];
    reg [4:0] valid_pipe, first_pipe, last_pipe,odd_first_pipe,parity_pipe;
    reg valid_after,last_after,parity_after,merge_pending,snapshot_pending;
    reg emitting;
    reg [OA-1:0] emit_idx, read_addr;
    reg signed [AW-1:0] read_data, read_data_b,read_data_c,read_data_d;
    reg read_valid;

    localparam PPW=IW+25;
    wire signed [15:0] lane_product[0:NO*2-1];
    genvar g;generate for(g=0;g<NO;g=g+1)begin:packed_mult
      wire signed [24:0] packed_w=weight_e[RW-1-g*25 -:25];
      wire signed [7:0] x=(g<NO/2)?data_e:data_b_e;
      (* use_dsp="yes" *) reg signed [32:0] packed_p;
      always @(posedge clk_i)packed_p<=packed_w*x;
      wire signed [15:0] hi=$signed(packed_p[32:16])+packed_p[15];
      assign lane_product[2*g]=packed_p[15:0];assign lane_product[2*g+1]=hi;
    end
    for(g=0;g<NO;g=g+1)begin:combine
      assign product[g]={lane_product[g][15],lane_product[g]}+{lane_product[g+NO][15],lane_product[g+NO]};
    end endgenerate
    genvar ch;generate for(ch=0;ch<NO;ch=ch+1)begin:interleaved
      reg signed [AW-1:0] even_acc,odd_acc;
      wire signed [AW-1:0] prod={{(AW-PW){product_r[ch][PW-1]}},product_r[ch]};
      wire signed [AW-1:0] bias={{(AW-8){biases[ch][7]}},biases[ch]};
      wire [AW-1:0] base=first_pipe[4]?bias:(odd_first_pipe[4]?{AW{1'b0}}:(parity_pipe[4]?odd_acc:even_acc));
      reg [11:0] low;reg [AW-12:0] upper_a,upper_b;
      wire [AW-12:0] upper_sum=upper_a+upper_b+low[11];
      reg [11:0] merge_low;reg [AW-12:0] merge_a,merge_b;
      wire [AW-12:0] merge_hi=merge_a+merge_b+merge_low[11];
      always @(posedge clk_i)begin
        if(valid_pipe[4])begin low<={1'b0,base[10:0]}+{1'b0,prod[10:0]};upper_a<=base[AW-1:11];upper_b<=prod[AW-1:11];end
        if(valid_after)begin if(parity_after)odd_acc<={upper_sum,low[10:0]};else even_acc<={upper_sum,low[10:0]};end
        if(merge_pending)begin merge_low<={1'b0,even_acc[10:0]}+{1'b0,odd_acc[10:0]};merge_a<=even_acc[AW-1:11];merge_b<=odd_acc[AW-1:11];end
        if(snapshot_pending)snapshot[ch]<={merge_hi,merge_low[10:0]};
      end
    end endgenerate
    integer j;
    always @(posedge clk_i) begin
        weight_r <= weights[addr_i];
        data_r <= data_i; data_b_r<=data_b_i;
        data_d <= data_r; data_b_d<=data_b_r; weight_d <= weight_r;
        data_e <= data_d; data_b_e<=data_b_d; weight_e <= weight_d;
        for(j=0;j<NO;j=j+1) begin
            product_r[j] <= product[j];
        end
        if(!rst_n_i) begin
            valid_pipe<=0; first_pipe<=0; last_pipe<=0;odd_first_pipe<=0;parity_pipe<=0;valid_after<=0;last_after<=0;parity_after<=0;merge_pending<=0;snapshot_pending<=0;
            emitting<=0; emit_idx<=0; read_valid<=0;
            valid_o<=0; done_o<=0; addr_o<=0; data_o<=0;
        end else begin
            valid_pipe <= {valid_pipe[3:0],valid_i};
            first_pipe <= {first_pipe[3:0],addr_i==0};
            last_pipe <= {last_pipe[3:0],addr_i==NI-1};
            odd_first_pipe<={odd_first_pipe[3:0],addr_i==1};parity_pipe<={parity_pipe[3:0],addr_i[0]};
            valid_after<=valid_pipe[4];last_after<=last_pipe[4];parity_after<=parity_pipe[4];
            merge_pending<=valid_after && last_after;snapshot_pending<=merge_pending;
            if(snapshot_pending)begin emitting<=1;emit_idx<=0;end
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
