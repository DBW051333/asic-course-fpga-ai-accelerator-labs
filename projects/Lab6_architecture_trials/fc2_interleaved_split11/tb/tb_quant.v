`timescale 1ns/1ps
module tb_quant;
 parameter real CLK_PERIOD=5.26;
 reg clk_i=0,rst_n_i=0,start_i=0;always #(CLK_PERIOD/2)clk_i=~clk_i;
 wire ready_o,done_o,v1,v2,v3;wire [7:0] d1;wire [7:0] d2,d2b,d2c,d2d;wire [7:0] d3;wire [6:0] a1;wire [4:0] a2;wire a3;
 wire signed [63:0] e1=$signed(d1),e2=$signed(d2),e2b=$signed(d2b),e2c=$signed(d2c),e2d=$signed(d2d),e3=$signed(d3);
 lab5_top dut(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.ready_o(ready_o),.done_o(done_o),
 .fc1_wren_o(v1),.fc1_data_o(d1),.fc1_addr_o(a1),.fc2_wren_o(v2),.fc2_data_o(d2),.fc2_data_b_o(d2b),.fc2_data_c_o(d2c),.fc2_data_d_o(d2d),.fc2_addr_o(a2),
 .fc3_wren_o(v3),.fc3_data_o(d3),.fc3_addr_o(a3));
 reg signed [63:0] ref1[0:6143],ref2[0:1535],ref3[0:95];reg [7:0] input_bytes[0:24575];reg [0:0] labels[0:41];
 integer job,gg,ll,i,errors=0,n1=0,n2=0,n3=0,completed=0,correct=0,ties=0,fd,pred;
 realtime launched[0:47],last_launch=0;integer min_latency=99999,max_latency=0,min_interval=99999,max_interval=0,cycles,interval;
 reg signed [63:0] score0;
 initial begin
  $readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc1_expected.mem",ref1);$readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc2_expected.mem",ref2);$readmemh("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/data/fc3_expected.mem",ref3);
  $readmemh("/home/ding/vivado_project/Lab5_truncation_optimization/data/all_inputs.mem",input_bytes);$readmemh("/home/ding/vivado_project/Lab5_truncation_optimization/data/labels.mem",labels);
  fd=$fopen("/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11/results/rtl_samples.csv","w");$fdisplay(fd,"sample,score0,score1,prediction,label,correct");
  repeat(5)@(negedge clk_i);rst_n_i=1;
  for(job=0;job<48;job=job+1)begin
   wait(ready_o);@(negedge clk_i);
   for(gg=0;gg<2;gg=gg+1)for(ll=0;ll<256;ll=ll+1) dut.u_fc1.inputs[gg][2047-ll*8 -:8]=input_bytes[job*512+gg*256+ll];
   start_i=1;launched[job]=$realtime+CLK_PERIOD/2;
   if(job>0)begin interval=$rtoi((launched[job]-last_launch)/CLK_PERIOD+0.5);if(interval<min_interval)min_interval=interval;if(interval>max_interval)max_interval=interval;end
   last_launch=launched[job];@(negedge clk_i);start_i=0;
  end
  wait(completed==48);repeat(3)@(negedge clk_i);
  if(n1!=6144 || n2!=1536 || n3!=96)begin errors=errors+1;$display("COUNT_FAIL %0d %0d %0d",n1,n2,n3);end
  $fclose(fd);
  $display("SUMMARY correct=%0d/42 ties=%0d errors=%0d values=%0d latency_cycles=%0d..%0d interval_cycles=%0d..%0d",correct,ties,errors,n1+n2+n3,min_latency,max_latency,min_interval,max_interval);
  if(errors==0)$display("PASS: 48 overlapping requests, 7776 layer outputs and addresses match");else $fatal(1,"FAIL errors=%0d",errors);
  $finish;
 end
 always @(posedge done_o)begin
  cycles=$rtoi(($realtime-launched[completed])/CLK_PERIOD+0.5);
  if(cycles<min_latency)min_latency=cycles;if(cycles>max_latency)max_latency=cycles;
  completed=completed+1;
 end
 always @(posedge clk_i)begin
  if(rst_n_i && v1)begin
   if(a1!==(n1%128) || e1!==ref1[n1])begin errors=errors+1;if(errors<10)$display("MISMATCH FC1[%0d] got=%0d expected=%0d addr=%0d",n1,e1,ref1[n1],a1);end n1=n1+1;
  end
  if(rst_n_i && v2)begin
   if(a2!==(n2%32) || e2!==ref2[n2] || e2b!==ref2[n2+1] || e2c!==ref2[n2+2] || e2d!==ref2[n2+3])begin errors=errors+1;if(errors<10)$display("MISMATCH FC2[%0d] got=%0d expected=%0d addr=%0d",n2,e2,ref2[n2],a2);end n2=n2+4;
  end
  if(rst_n_i && v3)begin
   if(a3!==(n3%2) || e3!==ref3[n3])begin errors=errors+1;if(errors<10)$display("MISMATCH FC3[%0d] got=%0d expected=%0d",n3,e3,ref3[n3]);end
   if(n3%2==0)score0=e3;
   else if(n3/2<42)begin
    pred=(score0<e3);if(pred==labels[n3/2])correct=correct+1;if(score0==e3)ties=ties+1;
    $fdisplay(fd,"%0d,%0d,%0d,%0d,%0d,%0d",n3/2,score0,e3,pred,labels[n3/2],pred==labels[n3/2]);
   end n3=n3+1;
  end
 end
 initial begin #2000000;$fatal(1,"FAIL TIMEOUT");end
endmodule
