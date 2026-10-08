`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 09/23/2026 06:26:38 PM
// Design Name: 
// Module Name: encoder
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


module encoder(
input [7:0] data,
output reg [2:0] code
    );
    always @(data)begin
    case(data)
    8'b00000001: code=0;
    8'b00000010: code=1;
    8'b00000100: code=2;
    8'b00001000: code=3;
    8'b00010000: code=4;
    8'b00100000: code=5;
    8'b01000000: code=6;
    8'b10000000: code=7;
    default:     code=3'bx;
    endcase
    end
    
endmodule
