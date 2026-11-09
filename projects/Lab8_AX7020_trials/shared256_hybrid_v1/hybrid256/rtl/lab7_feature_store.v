`timescale 1ns/1ps
// Three logical output RAMs share one physical byte-write BRAM.
// Words 0..15: FC1; 16..19: FC2; word 20 bytes 0..1: FC3.
// Simple dual-port inference, registered read + two pipeline stages = 3 cycles.
module lab7_feature_store(
 input wire clk_i,
 input wire [7:0] wr_mask_i,input wire [4:0] wr_addr_i,input wire [63:0] wr_data_i,
 input wire rd_en_i,input wire [4:0] rd_addr_i,output reg [63:0] rd_data_o);
 (* ram_style="block" *) reg [63:0] mem[0:31];
 reg [63:0] rd0,rd1;
 genvar b;generate for(b=0;b<8;b=b+1)begin:byte_write
  always @(posedge clk_i) if(wr_mask_i[b])mem[wr_addr_i][b*8 +:8]<=wr_data_i[b*8 +:8];
 end endgenerate
 reg [1:0] rd_en_pipe=0;
 always @(posedge clk_i)begin
  rd_en_pipe<={rd_en_pipe[0],rd_en_i};
  if(rd_en_i)rd0<=mem[rd_addr_i];
  if(rd_en_pipe[0])rd1<=rd0;
  if(rd_en_pipe[1])rd_data_o<=rd1;
 end
endmodule
