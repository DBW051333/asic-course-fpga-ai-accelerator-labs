`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 09/23/2026 05:52:00 PM
// Design Name: 
// Module Name: mux_4_to_1
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


module mux_4_to_1(
input a,
input b,
input c,
input d,
input [1:0] sel,

output reg q
    );
    always @(*)begin
        case(sel)
        2'd00: q=a;
        2'd01: q=b;
        2'd10: q=c;
        2'd11: q=d;
        endcase
    end
    
endmodule
