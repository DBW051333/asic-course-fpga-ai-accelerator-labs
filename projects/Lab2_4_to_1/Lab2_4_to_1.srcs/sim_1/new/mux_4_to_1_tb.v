`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 09/23/2026 05:59:39 PM
// Design Name: 
// Module Name: mux_4_to_1_tb
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


module mux_4_to_1_tb(

    );

reg         a;
reg         b;
reg         c;
reg         d;
reg [1:0]   sel;
wire        q;

mux_4_to_1 u_mux_4_to_1(
    .a(a),
    .b(b),
    .c(c),
    .d(d),
    .sel(sel),
    .q(q)
);

initial begin
    sel = 2'd0;
    a = 1'b1;
    b = 1'b0;
    c = 1'b1;
    d = 1'b0;

    #10; sel = 2'd1;
    #10; sel = 2'd2;
    #10; sel = 2'd3;
    #10; sel = 2'd0;
    #10; $finish;
end

endmodule
