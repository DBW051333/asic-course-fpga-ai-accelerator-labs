`timescale 1ns/1ps
module tb_lab8;
 parameter CLOCK_ENABLE=1,PREFETCH=1;
 parameter real CLK_PERIOD=6.0;
 reg clk_i=0,rst_n_i=0;always #(CLK_PERIOD/2)clk_i=~clk_i;
 reg [63:0] input_data_i=0;reg input_valid_i=0;wire input_ready_o;
 wire [63:0] output_data_o;wire [7:0] output_keep_o;wire output_last_o,output_valid_o;
 reg output_ready_i=0;wire [3:0] state_o;wire features_valid_o,infer_start_o,infer_done_o;
 wire [31:0] compute_cycles_o;
 reg [7:0] input_keep=8'hff;reg input_last=0;
 reg [5:0] awaddr=0,araddr=0;reg [2:0] prot=0;
 reg awvalid=0,wvalid=0,bready=0,arvalid=0,rready=0;
 reg [31:0] wdata=0;reg [3:0] wstrb=0;
 wire awready,wready,bvalid,arready,rvalid;wire [1:0] bresp,rresp;wire [31:0] rdata;
 lab8_npu dut(.aclk(clk_i),.aresetn(rst_n_i),
 .s_axis_tdata(input_data_i),.s_axis_tkeep(input_keep),.s_axis_tlast(input_last),.s_axis_tvalid(input_valid_i),.s_axis_tready(input_ready_o),
 .m_axis_tdata(output_data_o),.m_axis_tkeep(output_keep_o),.m_axis_tlast(output_last_o),.m_axis_tvalid(output_valid_o),.m_axis_tready(output_ready_i),
 .s_axi_awaddr(awaddr),.s_axi_awprot(prot),.s_axi_awvalid(awvalid),.s_axi_awready(awready),
 .s_axi_wdata(wdata),.s_axi_wstrb(wstrb),.s_axi_wvalid(wvalid),.s_axi_wready(wready),
 .s_axi_bresp(bresp),.s_axi_bvalid(bvalid),.s_axi_bready(bready),
 .s_axi_araddr(araddr),.s_axi_arprot(prot),.s_axi_arvalid(arvalid),.s_axi_arready(arready),
 .s_axi_rdata(rdata),.s_axi_rresp(rresp),.s_axi_rvalid(rvalid),.s_axi_rready(rready));
 assign state_o=dut.npu.state_o;assign features_valid_o=dut.npu.features_valid_o;
 assign infer_start_o=dut.infer_start;assign infer_done_o=dut.infer_done;assign compute_cycles_o=dut.npu_compute;
 task axi_address(input [5:0] addr);
  begin @(negedge clk_i);awaddr=addr;awvalid=1;@(posedge clk_i);while(!awready)@(posedge clk_i);@(negedge clk_i);awvalid=0;end
 endtask
 task axi_data(input [31:0] val,input [3:0] mask);
  begin @(negedge clk_i);wdata=val;wstrb=mask;wvalid=1;@(posedge clk_i);while(!wready)@(posedge clk_i);@(negedge clk_i);wvalid=0;end
 endtask
 task axi_write(input [5:0] addr,input [31:0] val,input [3:0] mask,input bit data_first);
  begin
   if(data_first)begin axi_data(val,mask);repeat(3)@(negedge clk_i);axi_address(addr);end
   else begin axi_address(addr);repeat(3)@(negedge clk_i);axi_data(val,mask);end
   wait(bvalid);repeat(4)begin @(negedge clk_i);if(!bvalid || bresp!==0)$fatal(1,"AXI B response not held");end
   bready=1;@(negedge clk_i);bready=0;
  end
 endtask
 task axi_check(input [5:0] addr,input [31:0] expected);
  reg [31:0] snapshot;begin
   @(negedge clk_i);araddr=addr;arvalid=1;@(posedge clk_i);while(!arready)@(posedge clk_i);@(negedge clk_i);arvalid=0;
   wait(rvalid);snapshot=rdata;
   repeat(4)begin @(negedge clk_i);if(!rvalid || rdata!==snapshot || rresp!==0)$fatal(1,"AXI R response not held");end
   if(snapshot!==expected)$fatal(1,"AXI register %h got %h expected %h",addr,snapshot,expected);
   rready=1;@(negedge clk_i);rready=0;
  end
 endtask
 reg [7:0] inputs[0:24575],gold[0:7775],predictions[0:47],labels[0:41];
 reg [63:0] words[0:1007];
 reg [63:0] exp_data[0:2047];reg [7:0] exp_keep[0:2047];reg exp_last[0:2047];
 integer nw=0,nr=0,errors=0,cycle=0,job=-1,starts=0,dones=0,correct=0;
 integer n1=0,n2=0,n3=0,values=0,feature_packets=0;
 integer stall_cycles=0,input_full_cycles=0,rx_empty_cycles=0,credit_full_cycles=0;
 integer feature_start_cycle=0,feature_cycles_total=0,feature_count=0;
 integer launch_cycle=0,min_compute=99999,max_compute=0,latency;
 integer fd,trace_fd,main_phase=0,j,k,b,old_starts;reg force_stall=0;
 reg [63:0] held_data;reg [7:0] held_keep;reg held_last,was_stalled=0;
 integer batch_phase=0,bj1=0,bj2=0,bj3=0,bn1=0,bn2=0,bn3=0,bvalues=0,bstarts=0,bdones=0,max_outstanding=0;
 integer map_sample[0:511],launch_times[0:511],last_launch=0,min_ii=99999,batch_begin;
 always @(posedge clk_i) if(rst_n_i && batch_phase)begin
  if(dut.npu.outstanding>max_outstanding)max_outstanding=dut.npu.outstanding;
  if(infer_start_o)begin
   launch_times[bstarts]=cycle;
   if(bstarts>0 && cycle-last_launch<min_ii)min_ii=cycle-last_launch;
   last_launch=cycle;bstarts=bstarts+1;
  end
  if(dut.npu.v1)begin
   if(dut.npu.a1!==bn1 || dut.npu.d1!==gold[map_sample[bj1]*162+bn1])$fatal(1,"BATCH FC1 job=%0d index=%0d",bj1,bn1);
   bvalues=bvalues+1;if(bn1==127)begin bn1=0;bj1=bj1+1;end else bn1=bn1+1;
  end
  if(dut.npu.v2)begin
   if(dut.npu.a2!==bn2 || {dut.npu.d2d,dut.npu.d2c,dut.npu.d2b,dut.npu.d2}!=={gold[map_sample[bj2]*162+131+bn2],gold[map_sample[bj2]*162+130+bn2],gold[map_sample[bj2]*162+129+bn2],gold[map_sample[bj2]*162+128+bn2]})$fatal(1,"BATCH FC2 job=%0d index=%0d",bj2,bn2);
   bvalues=bvalues+4;if(bn2==28)begin bn2=0;bj2=bj2+1;end else bn2=bn2+4;
  end
  if(dut.npu.v3)begin
   if(dut.npu.a3!==bn3 || dut.npu.d3!==gold[map_sample[bj3]*162+160+bn3])$fatal(1,"BATCH FC3 job=%0d index=%0d",bj3,bn3);
   bvalues=bvalues+1;if(bn3==1)begin bn3=0;bj3=bj3+1;end else bn3=1;
  end
  if(infer_done_o)begin
   if(cycle-launch_times[bdones]!=216 || compute_cycles_o!=216)$fatal(1,"BATCH latency %0d counter=%0d",cycle-launch_times[bdones],compute_cycles_o);
   bdones=bdones+1;
  end
 end
 task batch_run(input integer count,input integer gaps);
  integer sample,w,c,base,begin_cycle;reg [63:0] payload;begin
   base=bstarts;
   for(sample=0;sample<count;sample=sample+1)begin
    map_sample[base+sample]=sample%48;
    exp_data[nw]={40'd0,gold[(sample%48)*162+161],gold[(sample%48)*162+160],predictions[sample%48]};
    exp_keep[nw]=8'hff;exp_last[nw]=sample==count-1;nw=nw+1;
   end
   begin_cycle=cycle;send_word({32'(count),32'd3},0,0);
   for(sample=0;sample<count;sample=sample+1)for(w=0;w<64;w=w+1)begin
    payload=0;for(c=0;c<8;c=c+1)payload[c*8+:8]=inputs[(sample%48)*512+w*8+c];
    send_word(payload,gaps && w%11==3 ? 4 : 0,sample==count-1 && w==63);
   end
   wait(nr==nw);repeat(4)@(negedge clk_i);
   $display("BATCH count=%0d gaps=%0d cycles=%0d",count,gaps,cycle-begin_cycle);
   expect_features((count-1)%48);send_word(2,0);wait(nr==nw);repeat(4)@(negedge clk_i);
  end
 endtask
 task expect_byte(input [7:0] x);
  begin exp_data[nw]=x;exp_keep[nw]=1;exp_last[nw]=1;nw=nw+1;end
 endtask
 task expect_features(input integer s);
  integer t;begin for(t=0;t<21;t=t+1)begin
   exp_data[nw]=words[s*21+t];exp_keep[nw]=(t==20)?8'h03:8'hff;exp_last[nw]=(t==20);nw=nw+1;
  end feature_packets=feature_packets+1;end
 endtask
 task send_word(input [63:0] x,input integer gap,input bit last=1);
  begin
   repeat(gap)@(negedge clk_i);
   input_data_i=x;input_last=last;input_valid_i=1;
   @(posedge clk_i);while(!input_ready_o)@(posedge clk_i);
   @(negedge clk_i);input_valid_i=0;
  end
 endtask
 task send_sample(input integer s,input integer gaps);
  integer w,c;reg [63:0] payload;begin
   send_word(1,0,0);
   for(w=0;w<64;w=w+1)begin
    payload=0;for(c=0;c<8;c=c+1)payload[c*8 +:8]=inputs[s*512+w*8+c];
    send_word(payload,(gaps && w%11==3)?4:0,w==63);
   end
  end
 endtask
 task reset_system;
  begin @(negedge clk_i);rst_n_i=0;input_valid_i=0;repeat(5)@(negedge clk_i);rst_n_i=1;repeat(3)@(negedge clk_i);end
 endtask
 always @(negedge clk_i)begin
  if(main_phase)output_ready_i=!force_stall && (cycle%310>=150 && cycle%13!=0);
 end
 always @(posedge clk_i)begin
  cycle=cycle+1;
  if(!rst_n_i)was_stalled=0;
  else begin
   if(was_stalled && (output_data_o!==held_data || output_keep_o!==held_keep || output_last_o!==held_last || !output_valid_o))begin errors=errors+1;$display("FAIL stalled output changed cycle=%0d",cycle);end
   was_stalled=output_valid_o && !output_ready_i;
   held_data=output_data_o;held_keep=output_keep_o;held_last=output_last_o;
   if(output_valid_o && !output_ready_i)stall_cycles=stall_cycles+1;
   if(dut.npu.rx_full)input_full_cycles=input_full_cycles+1;
   if(state_o==1 && dut.npu.rx_empty)rx_empty_cycles=rx_empty_cycles+1;
   if(dut.npu.reserved==8)credit_full_cycles=credit_full_cycles+1;
   if(output_valid_o && output_ready_i)begin
    if(nr>=nw || output_data_o!==exp_data[nr] || output_keep_o!==exp_keep[nr] || output_last_o!==exp_last[nr])begin
     errors=errors+1;if(errors<12)$display("FAIL packet word=%0d got=%h/%h/%b expected=%h/%h/%b",nr,output_data_o,output_keep_o,output_last_o,exp_data[nr],exp_keep[nr],exp_last[nr]);
    end nr=nr+1;
   end
   if(main_phase)begin
    if(infer_start_o)begin job=job+1;starts=starts+1;launch_cycle=cycle;n1=0;n2=0;n3=0;end
    if(state_o==3)begin
     if((dut.npu.v1 && dut.npu.v2)||(dut.npu.v1 && dut.npu.v3)||(dut.npu.v2 && dut.npu.v3))begin errors=errors+1;$display("FAIL shared BRAM write collision");end
     if(dut.npu.v1)begin
      if(dut.npu.a1!==n1 || dut.npu.d1!==gold[job*162+n1])begin errors=errors+1;if(errors<12)$display("FAIL FC1 job=%0d addr=%0d",job,dut.npu.a1);end n1=n1+1;values=values+1;
     end
     if(dut.npu.v2)begin
      if(dut.npu.a2!==n2 || {dut.npu.d2d,dut.npu.d2c,dut.npu.d2b,dut.npu.d2}!=={gold[job*162+128+n2+3],gold[job*162+128+n2+2],gold[job*162+128+n2+1],gold[job*162+128+n2]})begin errors=errors+1;if(errors<12)$display("FAIL FC2 job=%0d addr=%0d",job,dut.npu.a2);end n2=n2+4;values=values+4;
     end
     if(dut.npu.v3)begin
      if(dut.npu.a3!==(n3%2) || dut.npu.d3!==gold[job*162+160+n3])begin errors=errors+1;if(errors<12)$display("FAIL FC3 job=%0d addr=%0d",job,dut.npu.a3);end n3=n3+1;values=values+1;
     end
    end
    if(infer_done_o)begin
     dones=dones+1;latency=cycle-launch_cycle;
     if(latency<min_compute)min_compute=latency;if(latency>max_compute)max_compute=latency;
     if(n1!=128 || n2!=32 || n3!=2)begin errors=errors+1;$display("FAIL feature counts %d %d %d",n1,n2,n3);end
     if(job<42 && predictions[job]==labels[job])correct=correct+1;
     $fdisplay(fd,"%0d,%0d,%0d,%0d,%0d",job,$signed(gold[job*162+160]),$signed(gold[job*162+161]),predictions[job],latency);
    end
    if(dut.npu.rd_issue && dut.npu.issue_idx==0)feature_start_cycle=cycle;
    if(dut.npu.feature_sent && dut.npu.send_idx==20)begin feature_cycles_total=feature_cycles_total+cycle-feature_start_cycle+1;feature_count=feature_count+1;end
    if(dut.npu.rd_valid_pipe[2] && !dut.npu.feature_q_ready)begin errors=errors+1;$display("FAIL read credit overflow");end
   end
  end
  if(trace_fd && cycle<2400)$fdisplay(trace_fd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",cycle,rst_n_i,state_o,input_valid_i,input_ready_o,dut.npu.rx_empty,dut.npu.tx_full,infer_start_o,infer_done_o,dut.npu.v1 && state_o==3,dut.npu.v2 && state_o==3,dut.npu.v3 && state_o==3,output_valid_o,output_ready_i,dut.npu.reserved);
 end
 initial begin
  $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/platform_v1/data/inputs.mem",inputs);$readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/platform_v1/data/features.mem",gold);$readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/platform_v1/data/feature_words.mem",words);$readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/platform_v1/data/predictions.mem",predictions);$readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/platform_v1/data/labels.mem",labels);
  fd=$fopen("results/samples.csv","w");$fdisplay(fd,"job,score0,score1,prediction,compute_cycles");
  trace_fd=$fopen("results/trace.csv","w");$fdisplay(trace_fd,"cycle,reset_n,state,in_valid,in_ready,in_empty,out_full,start,done,fc1_valid,fc2_valid,fc3_valid,out_valid,out_ready,reserved");
  reset_system;output_ready_i=1;
  axi_check(0,32'h4c414238);axi_check(12,166666672);
  axi_write(4,1,0,0);axi_check(0,32'h4c414238); // WSTRB=0 cannot reset.
  // Premature TLAST, bad TKEEP, late TLAST and command framing errors.
  expect_byte(8'he3);send_word(1,0,1);wait(nr==nw);
  expect_byte(8'he3);input_keep=8'h0f;send_word(2,0,1);input_keep=8'hff;wait(nr==nw);
  expect_byte(8'he3);send_word(1,0,0);send_word(64'hfe,0,1);wait(nr==nw);
  expect_byte(8'he3);send_word(1,0,0);repeat(64)send_word(0,0,0);send_word(0,0,1);wait(nr==nw);
  expect_byte(8'he3);send_word(2,0,0);send_word(0,0,1);wait(nr==nw);
  axi_check(20,5);axi_check(40,32'he3);axi_check(16,0);
  // A missing TLAST can be recovered with software reset. Address/data
  // order alternates; the reset must not cancel its own AXI B response.
  send_word(1,0,0);repeat(5)send_word(0,0,0);axi_write(4,1,1,1);axi_check(8,0);axi_check(20,0);
  // The read response for the live tick register must remain stable.
  @(negedge clk_i);araddr=48;arvalid=1;@(posedge clk_i);while(!arready)@(posedge clk_i);@(negedge clk_i);arvalid=0;
  wait(rvalid);begin reg [31:0] snap;snap=rdata;repeat(8)begin @(negedge clk_i);if(rdata!==snap || !rvalid)$fatal(1,"changing AXI read response");end end
  rready=1;@(negedge clk_i);rready=0;
  axi_write(4,1,1,0);
  expect_byte(8'he1);send_word(2,0);wait(nr==nw);
  expect_byte(8'he2);send_word(99,0);wait(nr==nw);
  // Reset a partial sample, then reset a running inference: neither may leave stale features.
  send_word(1,0,0);repeat(5)send_word(64'h0102030405060708,0,0);reset_system;
  send_sample(0,0);wait(infer_start_o);repeat(30)@(negedge clk_i);reset_system;
  expect_byte(8'he1);send_word(2,0);wait(nr==nw);
  @(negedge clk_i);main_phase=1;
  for(j=0;j<48;j=j+1)begin
   expect_byte(predictions[j]);expect_features(j);
   if(j==0 || j==47)expect_features(j);
   send_sample(j,1);send_word(2,0);if(j==0)begin force_stall=1;repeat(80)@(negedge clk_i);force_stall=0;end
   if(j==0 || j==47)send_word(2,0);
  end
  wait(nr==nw);repeat(20)@(negedge clk_i);
  if(starts!=48 || dones!=48 || values!=7776 || feature_count!=50 || correct!=42)begin errors=errors+1;$display("FAIL totals starts=%0d done=%0d values=%0d features=%0d correct=%0d",starts,dones,values,feature_count,correct);end
  if(stall_cycles==0 || rx_empty_cycles==0 || (PREFETCH && credit_full_cycles==0))begin errors=errors+1;$display("FAIL missing stall coverage");end
  axi_check(16,48);axi_check(20,1); // one no-history error after the final hard reset
  axi_check(24,216);axi_check(32,8);axi_check(36,162);axi_check(44,2);
  main_phase=0;batch_phase=1;output_ready_i=1;
  batch_run(42,0);batch_run(1,0);batch_run(3,1);
  fork
   batch_run(48,1);
   begin output_ready_i=0;repeat(3000)@(negedge clk_i);output_ready_i=1;end
  join
  if(bstarts!=94 || bdones!=94 || bvalues!=15228 || max_outstanding!=8)$fatal(1,"BATCH totals %0d %0d %0d credit=%0d",bstarts,bdones,bvalues,max_outstanding);
  $display("PASS BATCH INTEGRATED samples=%0d values=%0d min_ii=%0d max_outstanding=%0d",bdones,bvalues,min_ii,max_outstanding);
  batch_phase=0;
  // Invalid zero-size header is a legacy E2 command error; bad nonzero batch framing is E3.
  expect_byte(8'he2);send_word(3,0,1);wait(nr==nw);
  expect_byte(8'he2);send_word({32'd16384,32'd3},0,1);wait(nr==nw);
  expect_byte(8'he3);send_word({32'd2,32'd3},0,0);repeat(10)send_word(0,0,0);send_word(0,0,1);wait(nr==nw);
  expect_byte(8'he3);send_word({32'd1,32'd3},0,0);repeat(64)send_word(0,0,0);send_word(0,0,1);wait(nr==nw);
  // A malformed beat must wait while a previous batch result is stalled.
  output_ready_i=0;
  exp_data[nw]={40'd0,gold[161],gold[160],predictions[0]};exp_keep[nw]=8'hff;exp_last[nw]=0;nw=nw+1;
  expect_byte(8'he3);
  send_word({32'd2,32'd3},0,0);
  for(k=0;k<64;k=k+1)begin
   reg [63:0] payload;payload=0;for(b=0;b<8;b=b+1)payload[b*8+:8]=inputs[k*8+b];send_word(payload,0,0);
  end
  wait(output_valid_o);
  fork
   send_word(0,0,1);
   begin repeat(30)@(negedge clk_i);output_ready_i=1;end
  join
  wait(nr==nw);
  // Software reset during a missing-TLAST batch must preserve its AXI write response.
  send_word({32'd2,32'd3},0,0);repeat(10)send_word(0,0,0);axi_write(4,1,1,1);
  axi_check(8,0);axi_check(16,0);axi_check(20,0);
  expect_features(0); // Remove this expectation: reset invalidates history.
  nw=nw-21;
  expect_byte(8'he1);send_word(2,0);wait(nr==nw);
  expect_byte(predictions[0]);send_sample(0,0);wait(nr==nw);
  expect_features(0);send_word(2,0);wait(nr==nw);repeat(10)@(negedge clk_i);
  $display("SUMMARY CE=%0d PREFETCH=%0d jobs=%0d correct=%0d/42 values=%0d feature_packets=%0d output_words=%0d compute_cycles=%0d..%0d feature_cycles_total=%0d stalls=%0d input_full=%0d input_empty=%0d credit_full=%0d errors=%0d",CLOCK_ENABLE,PREFETCH,dones,correct,values,feature_count,nr,min_compute,max_compute,feature_cycles_total,stall_cycles,input_full_cycles,rx_empty_cycles,credit_full_cycles,errors);
  $fclose(fd);$fclose(trace_fd);
  if(errors)$fatal(1,"Lab7 regression failed");
  $display("PASS LAB8 AXIS AXILITE");$finish;
 end
 initial begin #300000;$fatal(1,"Timeout state=%0d packet=%0d nr=%0d nw=%0d jobs=%0d issued=%0d sent=%0d reserved=%0d rx=%b tx=%b rd=%b q=%b active=%b bank=%b credit=%0d",state_o,dut.packet_state,nr,nw,job,dut.npu.issue_idx,dut.npu.send_idx,dut.npu.reserved,dut.npu.rx_valid,dut.npu.tx_valid,dut.npu.rd_valid_pipe,dut.npu.feature_q_valid,dut.npu.receiving,dut.npu.bank_full,dut.npu.outstanding);end
endmodule
