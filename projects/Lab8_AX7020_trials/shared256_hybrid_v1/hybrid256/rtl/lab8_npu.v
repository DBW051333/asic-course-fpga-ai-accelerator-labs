`timescale 1ns/1ps
// One request/response at a time. Strict input packet framing; malformed
// packets reset the Lab7 datapath, drain through TLAST, then return E3.
module lab8_npu(
 (* X_INTERFACE_INFO="xilinx.com:signal:clock:1.0 aclk CLK", X_INTERFACE_PARAMETER="XIL_INTERFACENAME aclk, ASSOCIATED_BUSIF S_AXIS:M_AXIS:S_AXI, ASSOCIATED_RESET aresetn, FREQ_HZ 142857132" *) input wire aclk,
 (* X_INTERFACE_INFO="xilinx.com:signal:reset:1.0 aresetn RST", X_INTERFACE_PARAMETER="XIL_INTERFACENAME aresetn, POLARITY ACTIVE_LOW" *) input wire aresetn,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 S_AXIS TDATA" *) input wire [63:0] s_axis_tdata,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 S_AXIS TKEEP" *) input wire [7:0] s_axis_tkeep,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 S_AXIS TLAST" *) input wire s_axis_tlast,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 S_AXIS TVALID", X_INTERFACE_PARAMETER="XIL_INTERFACENAME S_AXIS, TDATA_NUM_BYTES 8, HAS_TKEEP 1, HAS_TLAST 1" *) input wire s_axis_tvalid,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 S_AXIS TREADY" *) output wire s_axis_tready,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 M_AXIS TDATA" *) output wire [63:0] m_axis_tdata,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 M_AXIS TKEEP" *) output wire [7:0] m_axis_tkeep,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 M_AXIS TLAST" *) output wire m_axis_tlast,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 M_AXIS TVALID", X_INTERFACE_PARAMETER="XIL_INTERFACENAME M_AXIS, TDATA_NUM_BYTES 8, HAS_TKEEP 1, HAS_TLAST 1" *) output wire m_axis_tvalid,
 (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 M_AXIS TREADY" *) input wire m_axis_tready,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI AWADDR" *) input wire [5:0] s_axi_awaddr,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI AWPROT" *) input wire [2:0] s_axi_awprot,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI AWVALID", X_INTERFACE_PARAMETER="XIL_INTERFACENAME S_AXI, PROTOCOL AXI4LITE, DATA_WIDTH 32, ADDR_WIDTH 6, READ_WRITE_MODE READ_WRITE" *) input wire s_axi_awvalid,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI AWREADY" *) output wire s_axi_awready,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI WDATA" *) input wire [31:0] s_axi_wdata,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI WSTRB" *) input wire [3:0] s_axi_wstrb,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI WVALID" *) input wire s_axi_wvalid,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI WREADY" *) output wire s_axi_wready,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI BRESP" *) output wire [1:0] s_axi_bresp,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI BVALID" *) output reg s_axi_bvalid,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI BREADY" *) input wire s_axi_bready,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI ARADDR" *) input wire [5:0] s_axi_araddr,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI ARPROT" *) input wire [2:0] s_axi_arprot,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI ARVALID" *) input wire s_axi_arvalid,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI ARREADY" *) output wire s_axi_arready,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI RDATA" *) output reg [31:0] s_axi_rdata,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI RRESP" *) output wire [1:0] s_axi_rresp,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI RVALID" *) output reg s_axi_rvalid,
 (* X_INTERFACE_INFO="xilinx.com:interface:aximm:1.0 S_AXI RREADY" *) input wire s_axi_rready
);
 localparam IDLE=0, RECEIVE=1, RESPONSE=2, DRAIN=3, ERROR=4;
 reg [2:0] packet_state;
 reg [6:0] payload_left;
 reg abort_reset,soft_reset,clear_stats;
 wire core_rst_n=aresetn && !abort_reset && !soft_reset;
 wire npu_in_ready,npu_out_valid,npu_out_last;
 wire [63:0] npu_out_data;
 wire [7:0] npu_out_keep;
 wire [3:0] npu_state;
 wire features_valid,infer_start,infer_done;
 wire [31:0] npu_compute;
 wire receiving=(packet_state==IDLE || packet_state==RECEIVE);
 wire expected_last=(packet_state==IDLE)?(s_axis_tdata!=64'd1):(payload_left==1);
 wire beat_ok=(s_axis_tkeep==8'hff && s_axis_tlast==expected_last);
 assign s_axis_tready=core_rst_n && ((packet_state==DRAIN) || (receiving && (beat_ok?npu_in_ready:1'b1)));
 wire rx_take=s_axis_tvalid && s_axis_tready;
 wire npu_in_valid=core_rst_n && receiving && s_axis_tvalid && beat_ok;
 wire npu_out_ready=(packet_state==RESPONSE) && m_axis_tready && core_rst_n;
 assign m_axis_tvalid=core_rst_n && ((packet_state==ERROR) || (packet_state==RESPONSE && npu_out_valid));
 assign m_axis_tdata=(packet_state==ERROR)?64'he3:npu_out_data;
 assign m_axis_tkeep=(packet_state==ERROR)?8'h01:npu_out_keep;
 assign m_axis_tlast=(packet_state==ERROR)?1'b1:npu_out_last;
 wire tx_take=m_axis_tvalid && m_axis_tready;
 lab7_top #(.CLOCK_ENABLE(1),.PREFETCH(1)) npu(
  .clk_i(aclk),.rst_n_i(core_rst_n),.input_data_i(s_axis_tdata),.input_valid_i(npu_in_valid),.input_ready_o(npu_in_ready),
  .output_data_o(npu_out_data),.output_keep_o(npu_out_keep),.output_last_o(npu_out_last),.output_valid_o(npu_out_valid),.output_ready_i(npu_out_ready),
  .state_o(npu_state),.features_valid_o(features_valid),.infer_start_o(infer_start),.infer_done_o(infer_done),.compute_cycles_o(npu_compute));
 function [31:0] byte_count(input [7:0] keep);
  integer i;begin byte_count=0;for(i=0;i<8;i=i+1)byte_count=byte_count+keep[i];end
 endfunction
 reg [31:0] tick,compute_start,request_start,rx_bytes,tx_bytes;
 reg [31:0] completed_jobs,error_count,last_compute,last_transaction,last_rx,last_tx,last_error,last_command;
 always @(posedge aclk)begin
  if(!aresetn || soft_reset)begin
   packet_state<=IDLE;payload_left<=0;abort_reset<=0;
   tick<=0;compute_start<=0;request_start<=0;rx_bytes<=0;tx_bytes<=0;
   completed_jobs<=0;error_count<=0;last_compute<=0;last_transaction<=0;last_rx<=0;last_tx<=0;last_error<=0;last_command<=0;
  end else begin
   tick<=tick+1'b1;abort_reset<=0;
   if(clear_stats)begin completed_jobs<=0;error_count<=0;last_error<=0;end
   if(infer_start)compute_start<=tick;
   if(infer_done)begin last_compute<=tick-compute_start;completed_jobs<=completed_jobs+1'b1;end
   if(rx_take)begin
    if(packet_state==IDLE)begin
     request_start<=tick;rx_bytes<=byte_count(s_axis_tkeep);tx_bytes<=0;last_command<=s_axis_tdata[31:0];
    end else rx_bytes<=rx_bytes+byte_count(s_axis_tkeep);
    if(receiving)begin
     if(!beat_ok)begin
      abort_reset<=1;error_count<=error_count+1'b1;last_error<=32'he3;
      packet_state<=s_axis_tlast?ERROR:DRAIN;
     end else if(packet_state==IDLE)begin
      payload_left<=64;packet_state<=(s_axis_tdata==1)?RECEIVE:RESPONSE;
     end else begin
      payload_left<=payload_left-1'b1;if(payload_left==1)packet_state<=RESPONSE;
     end
    end else if(packet_state==DRAIN && s_axis_tlast)packet_state<=ERROR;
   end
   if(tx_take)begin
    tx_bytes<=tx_bytes+byte_count(m_axis_tkeep);
    if(m_axis_tlast)begin
     packet_state<=IDLE;last_transaction<=tick-request_start+1'b1;last_rx<=rx_bytes;last_tx<=tx_bytes+byte_count(m_axis_tkeep);
     if(packet_state==RESPONSE && m_axis_tkeep==1 && m_axis_tdata[7:0]>=8'he1)begin
      error_count<=error_count+1'b1;last_error<={24'd0,m_axis_tdata[7:0]};
     end
    end
   end
  end
 end
 // AXI-Lite address/data channels are independent. Hold every response
 // until accepted, including across a software reset of the datapath.
 reg aw_pending,w_pending;
 reg [5:0] aw_hold;
 reg [31:0] w_hold;
 reg [3:0] strobe_hold;
 assign s_axi_awready=aresetn && !aw_pending && !s_axi_bvalid;
 assign s_axi_wready=aresetn && !w_pending && !s_axi_bvalid;
 assign s_axi_arready=aresetn && !s_axi_rvalid;
 assign s_axi_bresp=2'b00;assign s_axi_rresp=2'b00;
 reg [31:0] read_value;
 always @*begin
  case(s_axi_araddr[5:2])
   0:read_value=32'h4c414238;
   1:read_value=0;
   2:read_value={20'd0,packet_state,features_valid,npu_state,3'd0,(packet_state!=IDLE)};
   3:read_value=32'd142857132;
   4:read_value=completed_jobs;
   5:read_value=error_count;
   6:read_value=last_compute;
   7:read_value=last_transaction;
   8:read_value=last_rx;
   9:read_value=last_tx;
   10:read_value=last_error;
   11:read_value=last_command;
   12:read_value=tick;
   default:read_value=0;
  endcase
 end
 always @(posedge aclk)begin
  if(!aresetn)begin
   aw_pending<=0;w_pending<=0;aw_hold<=0;w_hold<=0;strobe_hold<=0;
   s_axi_bvalid<=0;s_axi_rvalid<=0;s_axi_rdata<=0;soft_reset<=0;clear_stats<=0;
  end else begin
   soft_reset<=0;clear_stats<=0;
   if(s_axi_awvalid && s_axi_awready)begin aw_pending<=1;aw_hold<=s_axi_awaddr;end
   if(s_axi_wvalid && s_axi_wready)begin w_pending<=1;w_hold<=s_axi_wdata;strobe_hold<=s_axi_wstrb;end
   if(aw_pending && w_pending && !s_axi_bvalid)begin
    aw_pending<=0;w_pending<=0;s_axi_bvalid<=1;
    if(aw_hold[5:2]==1 && strobe_hold[0])begin soft_reset<=w_hold[0];clear_stats<=w_hold[1];end
   end
   if(s_axi_bvalid && s_axi_bready)s_axi_bvalid<=0;
   if(s_axi_arvalid && s_axi_arready)begin s_axi_rvalid<=1;s_axi_rdata<=read_value;end
   if(s_axi_rvalid && s_axi_rready)s_axi_rvalid<=0;
  end
 end
endmodule
