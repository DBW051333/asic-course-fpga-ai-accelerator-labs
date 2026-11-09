`timescale 1ns/1ps
module tb_lab7;
 parameter CLOCK_ENABLE=1,PREFETCH=1;
 parameter real CLK_PERIOD=6.0;
 reg clk_i=0,rst_n_i=0;always #(CLK_PERIOD/2)clk_i=~clk_i;
 reg [63:0] input_data_i=0;reg input_valid_i=0;wire input_ready_o;
 wire [63:0] output_data_o;wire [7:0] output_keep_o;wire output_last_o,output_valid_o;
 reg output_ready_i=0;wire [3:0] state_o;wire features_valid_o,infer_start_o,infer_done_o;
 wire [31:0] compute_cycles_o;
 lab7_top #(.CLOCK_ENABLE(CLOCK_ENABLE),.PREFETCH(PREFETCH)) dut(.*);
 reg [7:0] inputs[0:24575],gold[0:7775],predictions[0:47],labels[0:41];
 reg [63:0] words[0:1007];
 reg [63:0] exp_data[0:2047];reg [7:0] exp_keep[0:2047];reg exp_last[0:2047];
 integer nw=0,nr=0,errors=0,cycle=0,job=-1,starts=0,dones=0,correct=0;
 integer n1=0,n2=0,n3=0,values=0,feature_packets=0;
 integer stall_cycles=0,input_full_cycles=0,rx_empty_cycles=0,credit_full_cycles=0;
 integer feature_start_cycle=0,feature_cycles_total=0,feature_count=0;
 integer launch_cycle=0,min_compute=99999,max_compute=0,latency;
 integer fd,trace_fd,main_phase=0,j,k,b,old_starts;
 reg [63:0] held_data;reg [7:0] held_keep;reg held_last,was_stalled=0;
 task expect_byte(input [7:0] x);
  begin exp_data[nw]=x;exp_keep[nw]=1;exp_last[nw]=1;nw=nw+1;end
 endtask
 task expect_features(input integer s);
  integer t;begin for(t=0;t<21;t=t+1)begin
   exp_data[nw]=words[s*21+t];exp_keep[nw]=(t==20)?8'h03:8'hff;exp_last[nw]=(t==20);nw=nw+1;
  end feature_packets=feature_packets+1;end
 endtask
 task send_word(input [63:0] x,input integer gap);
  begin
   repeat(gap)@(negedge clk_i);
   input_data_i=x;input_valid_i=1;
   @(posedge clk_i);while(!input_ready_o)@(posedge clk_i);
   @(negedge clk_i);input_valid_i=0;
  end
 endtask
 task send_sample(input integer s,input integer gaps);
  integer w,c;reg [63:0] payload;begin
   send_word(1,0);
   for(w=0;w<64;w=w+1)begin
    payload=0;for(c=0;c<8;c=c+1)payload[c*8 +:8]=inputs[s*512+w*8+c];
    send_word(payload,(gaps && w%11==3)?4:0);
   end
  end
 endtask
 task reset_system;
  begin @(negedge clk_i);rst_n_i=0;input_valid_i=0;repeat(5)@(negedge clk_i);rst_n_i=1;repeat(3)@(negedge clk_i);end
 endtask
 always @(negedge clk_i)begin
  if(main_phase)output_ready_i=(cycle%310>=150 && cycle%13!=0);
 end
 always @(posedge clk_i)begin
  cycle=cycle+1;
  if(!rst_n_i)was_stalled=0;
  else begin
   if(was_stalled && (output_data_o!==held_data || output_keep_o!==held_keep || output_last_o!==held_last || !output_valid_o))begin errors=errors+1;$display("FAIL stalled output changed cycle=%0d",cycle);end
   was_stalled=output_valid_o && !output_ready_i;
   held_data=output_data_o;held_keep=output_keep_o;held_last=output_last_o;
   if(output_valid_o && !output_ready_i)stall_cycles=stall_cycles+1;
   if(dut.rx_full)input_full_cycles=input_full_cycles+1;
   if(state_o==1 && dut.rx_empty)rx_empty_cycles=rx_empty_cycles+1;
   if(dut.reserved==8)credit_full_cycles=credit_full_cycles+1;
   if(output_valid_o && output_ready_i)begin
    if(nr>=nw || output_data_o!==exp_data[nr] || output_keep_o!==exp_keep[nr] || output_last_o!==exp_last[nr])begin
     errors=errors+1;if(errors<12)$display("FAIL packet word=%0d got=%h/%h/%b expected=%h/%h/%b",nr,output_data_o,output_keep_o,output_last_o,exp_data[nr],exp_keep[nr],exp_last[nr]);
    end nr=nr+1;
   end
   if(main_phase)begin
    if(infer_start_o)begin job=job+1;starts=starts+1;launch_cycle=cycle;n1=0;n2=0;n3=0;end
    if(state_o==3)begin
     if((dut.v1 && dut.v2)||(dut.v1 && dut.v3)||(dut.v2 && dut.v3))begin errors=errors+1;$display("FAIL shared BRAM write collision");end
     if(dut.v1)begin
      if(dut.a1!==n1 || dut.d1!==gold[job*162+n1])begin errors=errors+1;if(errors<12)$display("FAIL FC1 job=%0d addr=%0d",job,dut.a1);end n1=n1+1;values=values+1;
     end
     if(dut.v2)begin
      if(dut.a2!==n2 || {dut.d2d,dut.d2c,dut.d2b,dut.d2}!=={gold[job*162+128+n2+3],gold[job*162+128+n2+2],gold[job*162+128+n2+1],gold[job*162+128+n2]})begin errors=errors+1;if(errors<12)$display("FAIL FC2 job=%0d addr=%0d",job,dut.a2);end n2=n2+4;values=values+4;
     end
     if(dut.v3)begin
      if(dut.a3!==(n3%2) || dut.d3!==gold[job*162+160+n3])begin errors=errors+1;if(errors<12)$display("FAIL FC3 job=%0d addr=%0d",job,dut.a3);end n3=n3+1;values=values+1;
     end
    end
    if(infer_done_o)begin
     dones=dones+1;latency=cycle-launch_cycle;
     if(latency<min_compute)min_compute=latency;if(latency>max_compute)max_compute=latency;
     if(n1!=128 || n2!=32 || n3!=2)begin errors=errors+1;$display("FAIL feature counts %d %d %d",n1,n2,n3);end
     if(job<42 && predictions[job]==labels[job])correct=correct+1;
     $fdisplay(fd,"%0d,%0d,%0d,%0d,%0d",job,$signed(gold[job*162+160]),$signed(gold[job*162+161]),predictions[job],latency);
    end
    if(dut.rd_issue && dut.issue_idx==0)feature_start_cycle=cycle;
    if(dut.feature_sent && dut.send_idx==20)begin feature_cycles_total=feature_cycles_total+cycle-feature_start_cycle+1;feature_count=feature_count+1;end
    if(dut.rd_valid_pipe[2] && !dut.feature_q_ready)begin errors=errors+1;$display("FAIL read credit overflow");end
   end
  end
  if(trace_fd && cycle<2400)$fdisplay(trace_fd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",cycle,rst_n_i,state_o,input_valid_i,input_ready_o,dut.rx_empty,dut.tx_full,infer_start_o,infer_done_o,dut.v1 && state_o==3,dut.v2 && state_o==3,dut.v3 && state_o==3,output_valid_o,output_ready_i,dut.reserved);
 end
 initial begin
  $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/inputs.mem",inputs);$readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/features.mem",gold);$readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/feature_words.mem",words);$readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/predictions.mem",predictions);$readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/labels.mem",labels);
  fd=$fopen("results/samples.csv","w");$fdisplay(fd,"job,score0,score1,prediction,compute_cycles");
  trace_fd=$fopen("results/trace.csv","w");$fdisplay(trace_fd,"cycle,reset_n,state,in_valid,in_ready,in_empty,out_full,start,done,fc1_valid,fc2_valid,fc3_valid,out_valid,out_ready,reserved");
  reset_system;output_ready_i=1;
  expect_byte(8'he1);send_word(2,0);wait(nr==nw);
  expect_byte(8'he2);send_word(99,0);wait(nr==nw);
  // Reset a partial sample, then reset a running inference: neither may leave stale features.
  send_word(1,0);repeat(5)send_word(64'h0102030405060708,0);reset_system;
  send_sample(0,0);wait(infer_start_o);repeat(30)@(negedge clk_i);reset_system;
  expect_byte(8'he1);send_word(2,0);wait(nr==nw);
  @(negedge clk_i);main_phase=1;
  for(j=0;j<48;j=j+1)begin
   expect_byte(predictions[j]);expect_features(j);
   if(j==0 || j==47)expect_features(j);
   send_sample(j,1);send_word(2,0);
   if(j==0 || j==47)send_word(2,0);
  end
  wait(nr==nw);repeat(20)@(negedge clk_i);
  if(starts!=48 || dones!=48 || values!=7776 || feature_count!=50 || correct!=42)begin errors=errors+1;$display("FAIL totals starts=%0d done=%0d values=%0d features=%0d correct=%0d",starts,dones,values,feature_count,correct);end
  if(stall_cycles==0 || input_full_cycles==0 || rx_empty_cycles==0 || (PREFETCH && credit_full_cycles==0))begin errors=errors+1;$display("FAIL missing stall coverage");end
  $display("SUMMARY CE=%0d PREFETCH=%0d jobs=%0d correct=%0d/42 values=%0d feature_packets=%0d output_words=%0d compute_cycles=%0d..%0d feature_cycles_total=%0d stalls=%0d input_full=%0d input_empty=%0d credit_full=%0d errors=%0d",CLOCK_ENABLE,PREFETCH,dones,correct,values,feature_count,nr,min_compute,max_compute,feature_cycles_total,stall_cycles,input_full_cycles,rx_empty_cycles,credit_full_cycles,errors);
  $fclose(fd);$fclose(trace_fd);
  if(errors)$fatal(1,"Lab7 regression failed");
  $display("PASS LAB7");$finish;
 end
 initial begin #3000000;$fatal(1,"Timeout");end
endmodule
