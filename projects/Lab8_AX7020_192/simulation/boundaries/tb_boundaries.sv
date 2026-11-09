`timescale 1ns/1ps
module tb_boundaries;
reg clk=0,rst=0;always #3.5 clk=~clk;
reg [63:0] data=0;reg valid=0;wire ready;
lab7_top dut(.clk_i(clk),.rst_n_i(rst),.input_data_i(data),.input_valid_i(valid),.input_ready_o(ready),.output_ready_i(1'b1));
initial begin
 repeat(3)@(negedge clk);rst=1;
 @(negedge clk);data={32'd16383,32'd3};valid=1;
 @(posedge clk);while(!ready)@(posedge clk);
 @(negedge clk);valid=0;repeat(6)@(negedge clk);
 if(dut.batch_size!==14'd16383 || !dut.receiving || dut.state_r!=1)$fatal(1,"maximum header rejected");
 rst=0;repeat(3)@(negedge clk);rst=1;repeat(2)@(negedge clk);
 if(dut.receiving || dut.batch_size!=0)$fatal(1,"reset after maximum header failed");
 $display("PASS BOUNDARY maximum=16383 reset=ok");$finish;
end
initial begin #10000;$fatal(1,"watchdog");end
endmodule
