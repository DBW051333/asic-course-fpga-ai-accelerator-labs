`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 09/24/2026 10:35:01 AM
// Design Name: 
// Module Name: aync_fifo
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module aync_fifo#(
parameter DATA_WIDTH = 16,
parameter ADDR_WIDTH = 5
)(
input rst_n,
input wr_clk,
input rd_clk,
input wr_en,
input rd_en,
output reg [DATA_WIDTH - 1:0] rd_data,
input [DATA_WIDTH - 1:0] wr_data,
output reg valid,
output full,
output empty
    );
wire [ADDR_WIDTH-1:0] rd_addr;
wire [ADDR_WIDTH-1:0] wr_addr;
reg [ADDR_WIDTH:0] rd_addr_ptr;
reg [ADDR_WIDTH:0] wr_addr_ptr;

wire [ADDR_WIDTH:0] rd_addr_gray;
reg [ADDR_WIDTH:0] rd_addr_gray2;
reg [ADDR_WIDTH:0] rd_addr_gray3;

wire [ADDR_WIDTH:0] wr_addr_gray;
reg [ADDR_WIDTH:0] wr_addr_gray2;
reg [ADDR_WIDTH:0] wr_addr_gray3;

reg [DATA_WIDTH:0] fifo_mem [{ADDR_WIDTH{1'b1}}:0];
integer i;

always @(posedge wr_clk or negedge rst_n)begin
    if(!rst_n)begin
        for(i=0;i<={ADDR_WIDTH{1'b1}};i=i+1)begin
        fifo_mem[i] <= {DATA_WIDTH{1'd0}};
        end
    end
    else begin
        if(wr_en && (~full))begin
            fifo_mem[wr_addr] <= wr_data;
        end else begin
            fifo_mem[wr_addr] <= fifo_mem[wr_addr];
        end
    end
end

always @(posedge rd_clk or negedge rst_n)begin
    if(!rst_n)begin
        rd_data <= {DATA_WIDTH{1'd0}};
        valid <= 1'b0;
    end
    else begin
        if(rd_en & (~empty))begin
        rd_data <= fifo_mem[rd_addr];
        valid <= 1'b1;
        end
        else begin
        rd_data <= 'd0;
        valid <= 1'b0;
        end
    end
end
    
assign wr_addr = wr_addr_ptr[ADDR_WIDTH-1:0]; 
assign rd_addr = rd_addr_ptr[ADDR_WIDTH-1:0];

always @(posedge wr_clk, negedge rst_n)begin
    if(!rst_n)begin
        rd_addr_gray2 <= 'b0;
        rd_addr_gray3 <= 'b0;
    end
    else begin
        rd_addr_gray2 <= rd_addr_gray;
        rd_addr_gray3 <= rd_addr_gray2;
    end
end
    
always @(posedge rd_clk or negedge rst_n)begin
    if(!rst_n)begin
        wr_addr_gray2 <= 'b0;
        wr_addr_gray3 <= 'b0;
    end
    else begin
        wr_addr_gray2 <= wr_addr_gray;
        wr_addr_gray3 <= wr_addr_gray2;
    end
end
    
always @(posedge wr_clk or negedge rst_n)begin
    if(!rst_n)begin
    wr_addr_ptr <= 'h0;
    end
    else if(wr_en & (~full))begin
    wr_addr_ptr <= wr_addr_ptr + 1;
    end else begin
    wr_addr_ptr <= wr_addr_ptr;
    end
end

always @(posedge rd_clk or negedge rst_n)begin
    if(!rst_n)begin
    rd_addr_ptr <= 'h0;
    end
    else if(rd_en & (~empty))begin
    rd_addr_ptr <= rd_addr_ptr + 1;
    end else begin
    rd_addr_ptr <= rd_addr_ptr;
    end
end

assign wr_addr_gray = (wr_addr_ptr >> 1)^wr_addr_ptr;
assign rd_addr_gray = (rd_addr_ptr >> 1)^rd_addr_ptr;

assign full = (wr_addr_gray == {~(rd_addr_gray3[ADDR_WIDTH:ADDR_WIDTH-2]), rd_addr_gray3[ADDR_WIDTH-2:0]});
assign empty = (rd_addr_gray == wr_addr_gray3);


endmodule
