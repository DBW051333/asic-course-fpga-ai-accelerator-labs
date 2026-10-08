`timescale 1ns/1ps
module tb_lab5_top;
reg clk_i=0,rst_n_i=0,start_i=0;
always #5 clk_i=~clk_i;
wire done_o,v1,v2,v3;wire [31:0] d1;wire [47:0] d2,d2b,d2c,d2d;wire [63:0] d3;wire [6:0] a1;wire [4:0] a2;wire a3;
lab5_top dut(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.done_o(done_o),.fc1_wren_o(v1),.fc1_data_o(d1),.fc1_addr_o(a1),.fc2_wren_o(v2),.fc2_data_o(d2),.fc2_data_b_o(d2b),.fc2_data_c_o(d2c),.fc2_data_d_o(d2d),.fc2_addr_o(a2),.fc3_wren_o(v3),.fc3_data_o(d3),.fc3_addr_o(a3));
reg signed [63:0] ref1[0:127],ref2[0:31],ref3[0:1];
integer f,i,scan,errors=0,n1=0,n2=0,n3=0,job;time launched;
initial begin
 f=$fopen("/home/ding/vivado_project/Lab5/data/reference/fc1.txt","r");for(i=0;i<128;i=i+1) scan=$fscanf(f,"%d",ref1[i]);$fclose(f);
 f=$fopen("/home/ding/vivado_project/Lab5/data/reference/fc2.txt","r");for(i=0;i<32;i=i+1) scan=$fscanf(f,"%d",ref2[i]);$fclose(f);
 f=$fopen("/home/ding/vivado_project/Lab5/data/reference/fc3.txt","r");for(i=0;i<2;i=i+1) scan=$fscanf(f,"%d",ref3[i]);$fclose(f);
 repeat(5) @(negedge clk_i); rst_n_i=1;
 for(job=0;job<3;job=job+1) begin
  @(negedge clk_i);n1=0;n2=0;n3=0;start_i=1;launched=$time+5;
  @(negedge clk_i);start_i=0;
  @(posedge done_o); $display("MEASURE job=%0d elapsed_ns=%0d cycles=%0d",job,$time-launched,($time-launched)/10); repeat(3) @(negedge clk_i);
  if(n1!=128 || n2!=32 || n3!=2) begin errors=errors+1;$display("COUNT_FAIL %d %d %d",n1,n2,n3);end
  repeat(4) @(negedge clk_i);
 end
 if(errors==0)$display("PASS: three consecutive networks, all 486 values and addresses match");else $display("FAIL errors=%0d",errors);
 $finish;
end
always @(posedge clk_i) begin
 if(rst_n_i && v1)begin
  if(a1!==n1 || {{32{d1[31]}},d1}!==ref1[n1])begin errors=errors+1;$display("MISMATCH FC1[%0d] %d",n1,$signed(d1));end
  if(n1==127)$display("LAYER FC1 ns=%0d",$time-launched);n1=n1+1;
 end
 if(rst_n_i && v2)begin
  if(a2!==n2 || {{16{d2[47]}},d2}!==ref2[n2])begin errors=errors+1;$display("MISMATCH FC2[%0d] %d",n2,$signed(d2));end
  n2=n2+1;
  if({{16{d2b[47]}},d2b}!==ref2[n2])begin errors=errors+1;$display("MISMATCH FC2[%0d] %d",n2,$signed(d2b));end
  n2=n2+1;
  if({{16{d2c[47]}},d2c}!==ref2[n2])begin errors=errors+1;$display("MISMATCH FC2[%0d] %d",n2,$signed(d2c));end
  n2=n2+1;
  if({{16{d2d[47]}},d2d}!==ref2[n2])begin errors=errors+1;$display("MISMATCH FC2[%0d] %d",n2,$signed(d2d));end
  n2=n2+1;
 end
 if(rst_n_i && v3)begin
  if(a3!==n3 || d3!==ref3[n3])begin errors=errors+1;$display("MISMATCH FC3[%0d] %d",n3,$signed(d3));end
  $display("FC3[%0d]=%d",a3,$signed(d3));n3=n3+1;
 end
end
initial begin #2000000;$display("FAIL TIMEOUT");$finish;end
endmodule
