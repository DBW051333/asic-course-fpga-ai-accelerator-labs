`timescale 1ns/1ps
module lab7_feature_store(input wire clk_i,
 input wire v1,input wire [6:0] a1,input wire [7:0] d1,
 input wire v2,input wire [4:0] a2,input wire [7:0] d2,d2b,d2c,d2d,
 input wire v3,input wire a3,input wire [7:0] d3,
 input wire rd_en_i,input wire [4:0] rd_addr_i,output reg [63:0] rd_data_o);
 (* ram_style="block" *) reg [63:0] fc1[0:15];
 (* ram_style="distributed" *) reg [63:0] fc2[0:3];
 reg [15:0] fc3;
 genvar b;generate for(b=0;b<8;b=b+1)begin:byte_write
  always @(posedge clk_i) if(v1 && a1[2:0]==b)fc1[a1[6:3]][b*8 +:8]<=d1;
 end endgenerate
 always @(posedge clk_i)begin
  if(v2)begin if(a2[2])fc2[a2[4:3]][63:32]<={d2d,d2c,d2b,d2};else fc2[a2[4:3]][31:0]<={d2d,d2c,d2b,d2};end
  if(v3)begin if(a3)fc3[15:8]<=d3;else fc3[7:0]<=d3;end
 end
 reg [63:0] rd0,rd1,small0;reg [1:0] select_pipe;reg [1:0] rd_en_pipe=0;
 always @(posedge clk_i)begin
  rd_en_pipe<={rd_en_pipe[0],rd_en_i};
  if(rd_en_i)begin
   rd0<=fc1[rd_addr_i[3:0]];small0<=rd_addr_i==20 ? {48'd0,fc3} : fc2[rd_addr_i[1:0]];
   select_pipe[0]<=rd_addr_i>=16;
  end
  if(rd_en_pipe[0])begin rd1<=select_pipe[0]?small0:rd0;end
  if(rd_en_pipe[1])rd_data_o<=rd1;
 end
endmodule
