`timescale 1ns/1ps
module LUT6_2 #(parameter [63:0] INIT=0)(input wire I0,I1,I2,I3,I4,I5,output wire O5,O6);
assign O5=INIT[{1'b0,I4,I3,I2,I1,I0}];assign O6=INIT[{I5,I4,I3,I2,I1,I0}];endmodule
module CARRY4(input wire CI,CYINIT,input wire [3:0] DI,S,output wire [3:0] CO,O);
wire [4:0] c;assign c[0]=CI|CYINIT;
generate for(genvar i=0;i<4;i=i+1)begin:g assign c[i+1]=S[i]?c[i]:DI[i];assign CO[i]=c[i+1];assign O[i]=S[i]^c[i];end endgenerate
endmodule
