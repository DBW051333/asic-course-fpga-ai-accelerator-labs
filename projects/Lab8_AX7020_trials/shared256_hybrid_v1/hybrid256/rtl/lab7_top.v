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
 output wire infer_start_o,infer_done_o,output reg [31:0] compute_cycles_o
);
 localparam S_COMMAND=0,S_RECEIVE=1,S_START=2,S_RUN=3,S_RESULT=4,S_FEATURE=5,S_ERROR=6;
 reg [3:0] state_r,state_n;
 reg [5:0] load_idx;
 wire [63:0] rx_data;wire rx_valid,rx_ready,rx_full,rx_empty;
 wire tx_ready,tx_full,tx_empty;wire [72:0] tx_data;wire tx_valid;
 lab7_fifo #(.WIDTH(64),.ADDR_BITS(INPUT_FIFO_BITS)) input_fifo(
  .clk_i(clk_i),.rst_n_i(rst_n_i),.data_i(input_data_i),.valid_i(input_valid_i),.ready_o(input_ready_o),
  .data_o(rx_data),.valid_o(rx_valid),.ready_i(rx_ready),.full_o(rx_full),.empty_o(rx_empty));
 lab7_fifo #(.WIDTH(73),.ADDR_BITS(OUTPUT_FIFO_BITS)) output_fifo(
  .clk_i(clk_i),.rst_n_i(rst_n_i),.data_i(tx_data),.valid_i(tx_valid),.ready_o(tx_ready),
  .data_o({output_last_o,output_keep_o,output_data_o}),.valid_o(output_valid_o),.ready_i(output_ready_i),.full_o(tx_full),.empty_o(tx_empty));
 assign state_o=state_r;
 assign rx_ready=(state_r==S_COMMAND || state_r==S_RECEIVE);
 wire rx_take=rx_valid && rx_ready;
 assign infer_start_o=(state_r==S_START);
 wire compute_active=(state_r==S_START || state_r==S_RUN);
 wire core_ce=(!CLOCK_ENABLE) || compute_active;
 wire core_done,core_ready,v1,v2,v3;
 wire [7:0] d1,d2,d2b,d2c,d2d,d3;
 wire [6:0] a1;wire [4:0] a2;wire a3;
 lab7_core core(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(infer_start_o),.ce_i(core_ce),
  .load_we_i(state_r==S_RECEIVE && rx_take),.load_addr_i(load_idx),.load_data_i(rx_data),
  .done_o(core_done),.ready_o(core_ready),
  .fc1_wren_o(v1),.fc1_data_o(d1),.fc1_addr_o(a1),
  .fc2_wren_o(v2),.fc2_data_o(d2),.fc2_data_b_o(d2b),.fc2_data_c_o(d2c),.fc2_data_d_o(d2d),.fc2_addr_o(a2),
  .fc3_wren_o(v3),.fc3_data_o(d3),.fc3_addr_o(a3));
 assign infer_done_o=(state_r==S_RUN && core_done);
 reg signed [7:0] score0,score1;
 wire class_bit=score0<score1; // Ties are class zero, same as verified Lab6.
 reg [7:0] error_code;
 // The streaming layers emit at disjoint times; no write arbitration loses data.
 reg [7:0] feature_mask;reg [4:0] feature_wr_addr;reg [63:0] feature_wr_data;
 always @* begin
  feature_mask=0;feature_wr_addr=0;feature_wr_data=0;
  if(state_r==S_RUN)begin
   if(v1)begin feature_wr_addr={1'b0,a1[6:3]};feature_mask=8'b1<<a1[2:0];feature_wr_data={8{d1}};end
   else if(v2)begin feature_wr_addr=5'd16+{3'd0,a2[4:3]};feature_mask=a2[2]?8'hf0:8'h0f;feature_wr_data={2{d2d,d2c,d2b,d2}};end
   else if(v3)begin feature_wr_addr=20;feature_mask=a3?8'h02:8'h01;feature_wr_data={8{d3}};end
  end
 end
 wire [63:0] feature_rd_data;
 reg [4:0] issue_idx,send_idx;
 reg [3:0] reserved;
 wire rd_issue=(state_r==S_FEATURE && issue_idx<21 && reserved<8 && (PREFETCH || reserved==0));
 reg [2:0] rd_valid_pipe,rd_last_pipe;
 lab7_feature_store features(.clk_i(clk_i),.wr_mask_i(feature_mask),.wr_addr_i(feature_wr_addr),.wr_data_i(feature_wr_data),
  .rd_en_i(rd_issue),.rd_addr_i(issue_idx),.rd_data_o(feature_rd_data));
 wire feature_q_ready,feature_q_valid,feature_q_pop;
 wire [72:0] feature_q_data;
 // Mask unused FC3 bytes, so uninitialized BRAM bits never escape the interface.
 wire [63:0] clean_rd_data=rd_last_pipe[2]?{48'd0,feature_rd_data[15:0]}:feature_rd_data;
 lab7_fifo #(.WIDTH(73),.ADDR_BITS(3)) read_queue(
  .clk_i(clk_i),.rst_n_i(rst_n_i),
  .data_i({rd_last_pipe[2],rd_last_pipe[2]?8'h03:8'hff,clean_rd_data}),.valid_i(rd_valid_pipe[2]),.ready_o(feature_q_ready),
  .data_o(feature_q_data),.valid_o(feature_q_valid),.ready_i(feature_q_pop),.full_o(),.empty_o());
 assign feature_q_pop=(state_r==S_FEATURE && tx_ready);
 wire feature_sent=feature_q_valid && feature_q_pop;
 assign tx_valid=(state_r==S_RESULT || state_r==S_ERROR || (state_r==S_FEATURE && feature_q_valid));
 assign tx_data=(state_r==S_FEATURE)?feature_q_data:
                {1'b1,8'h01,56'd0,(state_r==S_ERROR)?error_code:{7'd0,class_bit}};
 // Three-part FSM: state register, next-state logic, state actions.
 always @(posedge clk_i)begin
  if(!rst_n_i)state_r<=S_COMMAND;else state_r<=state_n;
 end
 always @* begin
  state_n=state_r;
  case(state_r)
   S_COMMAND:if(rx_take)begin
    if(rx_data==64'd1)state_n=S_RECEIVE;
    else if(rx_data==64'd2 && features_valid_o)state_n=S_FEATURE;
    else state_n=S_ERROR;
   end
   S_RECEIVE:if(rx_take && load_idx==63)state_n=S_START;
   S_START:state_n=S_RUN;
   S_RUN:if(core_done)state_n=S_RESULT;
   S_RESULT,S_ERROR:if(tx_ready)state_n=S_COMMAND;
   S_FEATURE:if(feature_sent && send_idx==20)state_n=S_COMMAND;
   default:state_n=S_COMMAND;
  endcase
 end
 always @(posedge clk_i)begin
  if(!rst_n_i)begin
   load_idx<=0;features_valid_o<=0;compute_cycles_o<=0;score0<=0;score1<=0;error_code<=0;
   issue_idx<=0;send_idx<=0;reserved<=0;rd_valid_pipe<=0;rd_last_pipe<=0;
  end else begin
   rd_valid_pipe<={rd_valid_pipe[1:0],rd_issue};
   rd_last_pipe<={rd_last_pipe[1:0],rd_issue && issue_idx==20};
   if(state_r==S_COMMAND && rx_take)begin
    load_idx<=0;
    if(rx_data==1)features_valid_o<=0;
    if(rx_data==2 && features_valid_o)begin issue_idx<=0;send_idx<=0;reserved<=0;end
    error_code<=(rx_data==2)?8'he1:8'he2;
   end
   if(state_r==S_RECEIVE && rx_take)load_idx<=load_idx+1'b1;
   if(state_r==S_START)compute_cycles_o<=0;
   if(state_r==S_RUN)begin
    compute_cycles_o<=compute_cycles_o+1'b1;
    if(v3)begin if(a3)score1<=d3;else score0<=d3;end
    if(core_done)features_valid_o<=1;
   end
   if(rd_issue)issue_idx<=issue_idx+1'b1;
   if(feature_sent)send_idx<=send_idx+1'b1;
   if(state_r==S_FEATURE)case({rd_issue,feature_sent})
    2'b10:reserved<=reserved+1'b1;
    2'b01:reserved<=reserved-1'b1;
    default:reserved<=reserved;
   endcase
  end
 end
endmodule
