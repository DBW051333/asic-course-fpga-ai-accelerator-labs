`timescale 1ns/1ps
// Synchronous FIFO, first word visible when valid_o=1.
// Memory is not reset: pointer reset makes all old contents inaccessible.
module lab7_fifo #(parameter WIDTH=64, ADDR_BITS=4)(
 input wire clk_i,rst_n_i,
 input wire [WIDTH-1:0] data_i,input wire valid_i,output wire ready_o,
 output wire [WIDTH-1:0] data_o,output wire valid_o,input wire ready_i,
 output wire full_o,empty_o);
 localparam DEPTH=1<<ADDR_BITS;
 (* ram_style="distributed" *) reg [WIDTH-1:0] mem[0:DEPTH-1];
 reg [ADDR_BITS:0] wp,rp;
 wire push=valid_i && ready_o, pop=valid_o && ready_i;
 assign empty_o=(wp==rp);
 assign full_o=(wp[ADDR_BITS]!=rp[ADDR_BITS]) && (wp[ADDR_BITS-1:0]==rp[ADDR_BITS-1:0]);
 assign valid_o=rst_n_i && !empty_o;
 assign ready_o=rst_n_i && !full_o;
 assign data_o=mem[rp[ADDR_BITS-1:0]];
 always @(posedge clk_i)begin
  if(push)mem[wp[ADDR_BITS-1:0]]<=data_i;
  if(!rst_n_i)begin wp<=0;rp<=0;end
  else begin if(push)wp<=wp+1'b1;if(pop)rp<=rp+1'b1;end
 end
endmodule
