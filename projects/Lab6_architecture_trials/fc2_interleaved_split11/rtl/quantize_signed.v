// One quantization per completed layer. Nearest rounding ties toward +infinity.
module quantize_signed #(parameter IW=23,OW=8,SHIFT=10,ROUND=0,SAT=0)(
 input wire signed [IW-1:0] data_i,output wire signed [OW-1:0] data_o);
 localparam signed [IW:0] HALF=(SHIFT>0)?({{IW{1'b0}},1'b1} << (SHIFT-1)):0;
 localparam signed [IW:0] HIGH=({{IW{1'b0}},1'b1} << (OW-1))-1;
 localparam signed [IW:0] LOW=-({{IW{1'b0}},1'b1} << (OW-1));
 wire signed [IW:0] extended={data_i[IW-1],data_i};
 wire signed [IW:0] shifted=(extended+(ROUND?HALF:0)) >>> SHIFT;
 assign data_o=SAT?((shifted>HIGH)?HIGH[OW-1:0]:((shifted<LOW)?LOW[OW-1:0]:shifted[OW-1:0])):shifted[OW-1:0];
endmodule
