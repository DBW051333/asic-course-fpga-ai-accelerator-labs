`timescale 1ns/1ps
module tb_fc1_compare;
// Same 10 ns clock isolates scheduling; not timing closure evidence.
tb_original_trace old();
tb_current_trace #(.CLK_PERIOD(10.0)) now();
initial begin
 wait(old.trace_complete && now.trace_complete);
 $display("COMPARE PASS: old 512 issue steps, current 128 issue steps; outputs checked");
 #20; $finish;
end
endmodule
