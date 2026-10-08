`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 09/23/2026 06:31:13 PM
// Design Name: 
// Module Name: encoder_tb
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


module encoder_tb(

    );

reg [7:0] Data;
wire [2:0] Code;

encoder u_encoder(
    .data(Data),
    .code(Code)
);

initial begin
    Data = 8'b0;

    #10; Data = 8'b0000_0001;
    #10; Data = 8'b0000_0010;
    #10; Data = 8'b0000_0100;
    #10; Data = 8'b0000_1000;
    #10; Data = 8'b0001_0000;
    #10; Data = 8'b0010_0000;
    #10; Data = 8'b0100_0000;
    #10; Data = 8'b1000_0000;

    #10; Data = 8'b1000_0001;
    #10; $finish;
end

endmodule

