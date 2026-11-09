`timescale 1ns/1ps
// Lab7 word-stream NPU. One clock; ready/valid at both FIFO boundaries.
// CMD 1: 64 subsequent 64-bit words (512 signed bytes), return one class byte.
// CMD 2: read LAST completed features, 21 words, last keep=03 (162 bytes).
// Byte zero occupies bits 7:0. last/keep are packet metadata, never data bits.
module lab7_top #(
 parameter CLOCK_ENABLE=1, PREFETCH=1,
 parameter INPUT_FIFO_BITS=4, OUTPUT_FIFO_BITS=3
)(
 input wire clk_i,rst_n_i,
 input wire [63:0] input_data_i,input wire input_valid_i,output wire input_ready_o,
 output wire [63:0] output_data_o,output wire [7:0] output_keep_o,
 output wire output_last_o,output_valid_o,input wire output_ready_i,
 output wire [3:0] state_o,output reg features_valid_o,
 output wire infer_start_o,infer_done_o,output wire [31:0] compute_cycles_o
);
 localparam S_COMMAND=0,S_RECEIVE=1,S_START=2,S_RUN=3,S_RESULT=4,S_FEATURE=5,S_ERROR=6,S_DECODE=7;
 reg [3:0] state_r;
 reg [5:0] load_idx;reg [63:0] command_word;
 wire [63:0] rx_data;wire rx_valid,rx_ready,rx_full,rx_empty;
 wire tx_ready,tx_full,tx_empty;wire [72:0] tx_data;wire tx_valid;
 lab7_fifo #(.WIDTH(64),.ADDR_BITS(INPUT_FIFO_BITS)) input_fifo(
 .clk_i(clk_i),.rst_n_i(rst_n_i),.data_i(input_data_i),.valid_i(input_valid_i),.ready_o(input_ready_o),
 .data_o(rx_data),.valid_o(rx_valid),.ready_i(rx_ready),.full_o(rx_full),.empty_o(rx_empty));
 lab7_fifo #(.WIDTH(73),.ADDR_BITS(OUTPUT_FIFO_BITS)) output_fifo(
 .clk_i(clk_i),.rst_n_i(rst_n_i),.data_i(tx_data),.valid_i(tx_valid),.ready_o(tx_ready),
 .data_o({output_last_o,output_keep_o,output_data_o}),.valid_o(output_valid_o),.ready_i(output_ready_i),.full_o(tx_full),.empty_o(tx_empty));
 reg batch_mode,receiving,flush_pipeline;
 reg [13:0] batch_size,received_count,launched_count,completed_count;
 reg [1:0] bank_full;
 reg write_bank,read_bank,locked_bank,locked_valid;
 reg [3:0] outstanding;
 reg signed [7:0] score0;
 reg [7:0] error_code;
 reg [31:0] tick,last_cycles,start_ticks[0:7];
 reg [2:0] start_head,start_tail;
 assign state_o=state_r;
 wire core_done,core_ready,v1,v2,v3;
 wire [63:0] feature_rd_data;
 wire compute_active=state_r==S_RECEIVE || state_r==S_RUN;
 wire core_ce=(!CLOCK_ENABLE) || compute_active || flush_pipeline;
 assign rx_ready=state_r==S_COMMAND || (compute_active && receiving && !bank_full[write_bank] && !(locked_valid && locked_bank==write_bank));
 wire rx_take=rx_valid && rx_ready;
 wire result_fire=output_valid_o && output_ready_i && output_keep_o==(batch_mode?8'hff:8'h01) && compute_active;
 wire launch=compute_active && launched_count<batch_size && core_ready && bank_full[read_bank] && (outstanding<8 || result_fire);
 wire release_bank=locked_valid && core_ready;
 assign infer_start_o=launch;
 assign infer_done_o=compute_active && core_done && launched_count>completed_count;
 assign compute_cycles_o=infer_done_o ? tick-start_ticks[start_head] : last_cycles;

 wire [7:0] d1,d2,d2b,d2c,d2d,d3;
 wire [6:0] a1;wire [4:0] a2;wire a3;
 lab7_core core(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(launch),.ce_i(core_ce),
  .load_bank_i(write_bank),.input_bank_i(read_bank),.load_we_i((state_r==S_RECEIVE || state_r==S_RUN) && rx_take),.load_addr_i(load_idx),.load_data_i(rx_data),
  .done_o(core_done),.ready_o(core_ready),
  .fc1_wren_o(v1),.fc1_data_o(d1),.fc1_addr_o(a1),
  .fc2_wren_o(v2),.fc2_data_o(d2),.fc2_data_b_o(d2b),.fc2_data_c_o(d2c),.fc2_data_d_o(d2d),.fc2_addr_o(a2),
  .fc3_wren_o(v3),.fc3_data_o(d3),.fc3_addr_o(a3));
 reg [4:0] issue_idx,send_idx;
 reg [3:0] reserved;
 wire rd_issue=(state_r==S_FEATURE && issue_idx<21 && reserved<8 && (PREFETCH || reserved==0));
 reg [2:0] rd_valid_pipe,rd_last_pipe;
 lab7_feature_store features(.clk_i(clk_i),.v1(v1 && compute_active),.a1(a1),.d1(d1),
  .v2(v2 && compute_active),.a2(a2),.d2(d2),.d2b(d2b),.d2c(d2c),.d2d(d2d),
  .v3(v3 && compute_active),.a3(a3),.d3(d3),
  .rd_en_i(rd_issue),.rd_addr_i(issue_idx),.rd_data_o(feature_rd_data));
 wire feature_q_ready,feature_q_valid,feature_q_pop;
 wire [72:0] feature_q_data;
 // Mask unused FC3 bytes, so uninitialized BRAM bits never escape the interface.
 wire [63:0] clean_rd_data=rd_last_pipe[2]?{48'd0,feature_rd_data[15:0]}:feature_rd_data;
 lab7_fifo #(.WIDTH(73),.ADDR_BITS(3)) read_queue(
  .clk_i(clk_i),.rst_n_i(rst_n_i),
  .data_i({rd_last_pipe[2],rd_last_pipe[2]?8'h03:8'hff,clean_rd_data}),.valid_i(rd_valid_pipe[2]),.ready_o(feature_q_ready),
  .data_o(feature_q_data),.valid_o(feature_q_valid),.ready_i(feature_q_pop),.full_o(),.empty_o());
 assign feature_q_pop=state_r==S_FEATURE && tx_ready;
 wire feature_sent=feature_q_valid && feature_q_pop;
 assign tx_valid=(infer_done_o || state_r==S_ERROR || (state_r==S_FEATURE && feature_q_valid));
 wire final_result=completed_count+14'd1==batch_size;
 wire [63:0] result_word=batch_mode ? {40'd0,d3,score0,7'd0,(score0<$signed(d3))} : {56'd0,7'd0,(score0<$signed(d3))};
 assign tx_data=state_r==S_FEATURE ? feature_q_data : state_r==S_ERROR ? {1'b1,8'h01,56'd0,error_code} : {final_result,batch_mode?8'hff:8'h01,result_word};
 always @(posedge clk_i)begin
  if(!rst_n_i)begin
   flush_pipeline<=0;state_r<=S_COMMAND;load_idx<=0;features_valid_o<=0;batch_mode<=0;batch_size<=0;
   receiving<=0;received_count<=0;launched_count<=0;completed_count<=0;
   bank_full<=0;write_bank<=0;read_bank<=0;locked_bank<=0;locked_valid<=0;outstanding<=0;
   score0<=0;error_code<=0;tick<=0;last_cycles<=0;start_head<=0;start_tail<=0;
   issue_idx<=0;send_idx<=0;reserved<=0;rd_valid_pipe<=0;rd_last_pipe<=0;
  end else begin
   tick<=tick+1'b1;flush_pipeline<=infer_done_o && final_result;
   rd_valid_pipe<={rd_valid_pipe[1:0],rd_issue};
   rd_last_pipe<={rd_last_pipe[1:0],rd_issue && issue_idx==20};
   // Break the FIFO read-pointer -> header decode -> counter reset path.
   if(state_r==S_COMMAND && rx_take)begin command_word<=rx_data;state_r<=S_DECODE;end
   if(state_r==S_DECODE)begin
    if(command_word==1 || (command_word[31:0]==3 && command_word[63:46]==0 && command_word[45:32]!=0))begin
     batch_mode<=command_word[1];batch_size<=command_word[1] ? command_word[45:32] : 14'd1;
     receiving<=1;received_count<=0;launched_count<=0;completed_count<=0;load_idx<=0;
     bank_full<=0;write_bank<=0;read_bank<=0;locked_valid<=0;outstanding<=0;
     start_head<=0;start_tail<=0;features_valid_o<=0;state_r<=S_RECEIVE;
    end else if(command_word==2 && features_valid_o)begin state_r<=S_FEATURE;issue_idx<=0;send_idx<=0;reserved<=0;end
    else begin state_r<=S_ERROR;error_code<=command_word==2 ? 8'he1:8'he2;end
   end
   if(compute_active && rx_take)begin
    if(load_idx==63)begin
     bank_full[write_bank]<=1;write_bank<=!write_bank;load_idx<=0;
     received_count<=received_count+1;
     if(received_count+14'd1==batch_size)receiving<=0;
    end else load_idx<=load_idx+1'b1;
   end
   if(release_bank)begin bank_full[locked_bank]<=0;locked_valid<=0;end
   if(launch)begin
    state_r<=S_RUN;launched_count<=launched_count+1;locked_bank<=read_bank;locked_valid<=1;read_bank<=!read_bank;
    start_ticks[start_tail]<=tick;start_tail<=start_tail+1'b1;
   end
   case({launch,result_fire})
    2'b10:outstanding<=outstanding+1'b1;
    2'b01:outstanding<=outstanding-1'b1;
    default:begin end
   endcase
   if(compute_active && v3 && !a3)score0<=d3;
   if(infer_done_o)begin
    last_cycles<=tick-start_ticks[start_head];start_head<=start_head+1'b1;completed_count<=completed_count+1;
    if(final_result)begin features_valid_o<=1;state_r<=S_COMMAND;end
   end
   if(state_r==S_ERROR && tx_ready)state_r<=S_COMMAND;
   if(rd_issue)issue_idx<=issue_idx+1'b1;
   if(feature_sent)begin send_idx<=send_idx+1'b1;if(send_idx==20)state_r<=S_COMMAND;end
   if(state_r==S_FEATURE)case({rd_issue,feature_sent})
    2'b10:reserved<=reserved+1'b1;
    2'b01:reserved<=reserved-1'b1;
    default:reserved<=reserved;
   endcase
  end
 end
endmodule
