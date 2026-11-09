`timescale 1ns/1ps
// Actual configured AMD AXI DMA + NPU, with an AXI DDR byte-memory model.
// PS software is represented by AXI-Lite register transactions.
module tb_lab8_dma;
 reg clk=0,rst_n=0;always #3.0 clk=~clk;
 reg [9:0] la=0,lr=0;reg lav=0,lwv=0,lrv=0;reg [31:0] ld=0;
 wire lar,lwr,lbv,lrr,lrdv;wire [31:0] lrd;wire [1:0] lbr,lrrsp;
 wire [31:0] ra,wa;wire [7:0] rlen,wlen;wire [2:0] rsize,wsize;wire [1:0] rburst,wburst;
 wire rav,wav,rr,wwv,wwlast,br;wire [63:0] wd;wire [7:0] ws;
 wire [63:0] indata,outdata;wire [7:0] inkeep,outkeep;wire inv,inready,inlast,outv,outready,outlast;
 reg read_active=0,write_active=0,bvalid=0;
 reg [31:0] read_addr=0,write_addr=0;reg [8:0] read_left=0,write_left=0;
 reg [7:0] memory[0:65535],inputs[0:24575],gold[0:7775],pred[0:47];
 integer cycle=0,errors=0,checked=0,job,j,k,q,fd;
 wire raready=!read_active && cycle%7!=0;
 wire waready=!write_active && !bvalid && cycle%9!=0;
 wire wready=write_active && cycle%13!=0;
 wire [63:0] rd={memory[read_addr+7],memory[read_addr+6],memory[read_addr+5],memory[read_addr+4],memory[read_addr+3],memory[read_addr+2],memory[read_addr+1],memory[read_addr]};
 lab8_system_axi_dma_0_0 dma(
 .s_axi_lite_aclk(clk),.m_axi_mm2s_aclk(clk),.m_axi_s2mm_aclk(clk),.axi_resetn(rst_n),
 .s_axi_lite_awaddr(la),.s_axi_lite_awvalid(lav),.s_axi_lite_awready(lar),
 .s_axi_lite_wdata(ld),.s_axi_lite_wvalid(lwv),.s_axi_lite_wready(lwr),
 .s_axi_lite_bvalid(lbv),.s_axi_lite_bready(1'b1),.s_axi_lite_bresp(lbr),
 .s_axi_lite_araddr(lr),.s_axi_lite_arvalid(lrv),.s_axi_lite_arready(lrr),
 .s_axi_lite_rdata(lrd),.s_axi_lite_rvalid(lrdv),.s_axi_lite_rready(1'b1),.s_axi_lite_rresp(lrrsp),
 .m_axi_mm2s_araddr(ra),.m_axi_mm2s_arlen(rlen),.m_axi_mm2s_arsize(rsize),.m_axi_mm2s_arburst(rburst),.m_axi_mm2s_arvalid(rav),.m_axi_mm2s_arready(raready),
 .m_axi_mm2s_rdata(rd),.m_axi_mm2s_rvalid(read_active),.m_axi_mm2s_rlast(read_left==1),.m_axi_mm2s_rresp(2'b00),.m_axi_mm2s_rready(rr),
 .m_axis_mm2s_tdata(indata),.m_axis_mm2s_tkeep(inkeep),.m_axis_mm2s_tlast(inlast),.m_axis_mm2s_tvalid(inv),.m_axis_mm2s_tready(inready),
 .m_axi_s2mm_awaddr(wa),.m_axi_s2mm_awlen(wlen),.m_axi_s2mm_awsize(wsize),.m_axi_s2mm_awburst(wburst),.m_axi_s2mm_awvalid(wav),.m_axi_s2mm_awready(waready),
 .m_axi_s2mm_wdata(wd),.m_axi_s2mm_wstrb(ws),.m_axi_s2mm_wlast(wwlast),.m_axi_s2mm_wvalid(wwv),.m_axi_s2mm_wready(wready),
 .m_axi_s2mm_bvalid(bvalid),.m_axi_s2mm_bresp(2'b00),.m_axi_s2mm_bready(br),
 .s_axis_s2mm_tdata(outdata),.s_axis_s2mm_tkeep(outkeep),.s_axis_s2mm_tlast(outlast),.s_axis_s2mm_tvalid(outv),.s_axis_s2mm_tready(outready));
 lab8_npu npu(.aclk(clk),.aresetn(rst_n),
 .s_axis_tdata(indata),.s_axis_tkeep(inkeep),.s_axis_tlast(inlast),.s_axis_tvalid(inv),.s_axis_tready(inready),
 .m_axis_tdata(outdata),.m_axis_tkeep(outkeep),.m_axis_tlast(outlast),.m_axis_tvalid(outv),.m_axis_tready(outready),
 .s_axi_awaddr(6'd0),.s_axi_awprot(3'd0),.s_axi_awvalid(1'b0),.s_axi_wdata(32'd0),.s_axi_wstrb(4'd0),.s_axi_wvalid(1'b0),.s_axi_bready(1'b1),
 .s_axi_araddr(6'd0),.s_axi_arprot(3'd0),.s_axi_arvalid(1'b0),.s_axi_rready(1'b1));
 always @(posedge clk)begin
  cycle<=cycle+1;
  if(!rst_n)begin read_active<=0;write_active<=0;bvalid<=0;end
  else begin
   if(rav && raready)begin
    if(rsize!=3 || rburst!=1 || rlen>15)$fatal(1,"Unexpected MM2S burst");
    read_active<=1;read_addr<=ra;read_left<=rlen+1'b1;
   end
   if(read_active && rr)begin
    read_addr<=read_addr+8;read_left<=read_left-1'b1;if(read_left==1)read_active<=0;
   end
   if(wav && waready)begin
    if(wsize!=3 || wburst!=1 || wlen>15)$fatal(1,"Unexpected S2MM burst");
    write_active<=1;write_addr<=wa;write_left<=wlen+1'b1;
   end
   if(wwv && wready)begin
    for(q=0;q<8;q=q+1)if(ws[q])memory[write_addr+q]<=wd[q*8+:8];
    if(wwlast!==(write_left==1))$fatal(1,"S2MM WLAST mismatch");
    write_addr<=write_addr+8;write_left<=write_left-1'b1;
    if(write_left==1)begin write_active<=0;bvalid<=1;end
   end
   if(bvalid && br)bvalid<=0;
  end
 end
 task dma_write(input [9:0] addr,input [31:0] value);
  begin
   fork
    begin @(negedge clk);la=addr;lav=1;@(posedge clk);while(!lar)@(posedge clk);@(negedge clk);lav=0;end
    begin @(negedge clk);ld=value;lwv=1;@(posedge clk);while(!lwr)@(posedge clk);@(negedge clk);lwv=0;end
   join
   wait(lbv);if(lbr!==0)$fatal(1,"DMA AXI write response");@(negedge clk);
  end
 endtask
 task dma_read(input [9:0] addr,output [31:0] value);
  begin
   @(negedge clk);lr=addr;lrv=1;@(posedge clk);while(!lrr)@(posedge clk);@(negedge clk);lrv=0;
   wait(lrdv);value=lrd;if(lrrsp!==0)$fatal(1,"DMA AXI read response");@(negedge clk);
  end
 endtask
 task exchange(input integer txsize,input integer capacity,input integer expected_bytes);
  integer tries;reg [31:0] sendstatus,recvstatus,length;begin
   for(k=0;k<176;k=k+1)memory['h2000+k]=8'ha5;
   dma_write('h48,'h2000);dma_write('h58,capacity);
   dma_write('h18,'h1000);dma_write('h28,txsize);
   tries=0;sendstatus=0;recvstatus=0;
   while(!(sendstatus[1] && recvstatus[1]))begin
    dma_read('h04,sendstatus);dma_read('h34,recvstatus);
    if((sendstatus & 'h70)||(recvstatus & 'h70))$fatal(1,"DMA error send=%h recv=%h",sendstatus,recvstatus);
    tries=tries+1;if(tries>3000)$fatal(1,"DMA timeout send=%h recv=%h",sendstatus,recvstatus);
   end
   dma_read('h58,length);
   if(length!=expected_bytes)$fatal(1,"DMA received bytes=%0d expected=%0d",length,expected_bytes);
   for(k=expected_bytes;k<176;k=k+1)if(memory['h2000+k]!==8'ha5)$fatal(1,"DMA wrote beyond valid bytes at %0d",k);
  end endtask
 initial begin
  $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/platform_v1/data/inputs.mem",inputs);
  $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/platform_v1/data/features.mem",gold);
  $readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/platform_v1/data/predictions.mem",pred);
  fd=$fopen("results/dma_samples.csv","w");$fdisplay(fd,"sample,prediction,compute_cycles,features_checked");
  repeat(20)@(negedge clk);rst_n=1;repeat(50)@(negedge clk);
  dma_write(0,1);dma_write('h30,1);
  // Error replies are also genuine one-byte DMA packets.
  memory['h1000]=2;for(k=1;k<8;k=k+1)memory['h1000+k]=0;
  exchange(8,168,1);if(memory['h2000]!==8'he1)$fatal(1,"No-history response");
  memory['h1000]=1;exchange(8,8,1);if(memory['h2000]!==8'he3)$fatal(1,"Malformed packet response");
  for(job=0;job<42;job=job+1)begin
   memory['h1000]=1;for(k=1;k<8;k=k+1)memory['h1000+k]=0;
   for(k=0;k<512;k=k+1)memory['h1008+k]=inputs[job*512+k];
   exchange(520,8,1);
   if(memory['h2000]!==pred[job])$fatal(1,"DMA classification sample %0d",job);
   if(npu.last_compute!=216 || npu.last_rx!=520 || npu.last_tx!=1)$fatal(1,"Inference hardware counters");
   memory['h1000]=2;exchange(8,168,162);
   for(k=0;k<162;k=k+1)begin
    if(memory['h2000+k]!==gold[job*162+k])$fatal(1,"DMA feature mismatch sample=%0d index=%0d",job,k);
    checked=checked+1;
   end
   if(npu.last_rx!=8 || npu.last_tx!=162)$fatal(1,"Feature hardware counters");
   $fdisplay(fd,"%0d,%0d,%0d,162",job,pred[job],npu.last_compute);
  end
  if(npu.completed_jobs!=42 || npu.error_count!=2)$fatal(1,"DMA/NPU totals");
  $fclose(fd);$display("PASS LAB8 ACTUAL DMA samples=42 features=%0d errors=0",checked);$finish;
 end
 initial begin #5000000;$fatal(1,"DMA integration timeout");end
endmodule
