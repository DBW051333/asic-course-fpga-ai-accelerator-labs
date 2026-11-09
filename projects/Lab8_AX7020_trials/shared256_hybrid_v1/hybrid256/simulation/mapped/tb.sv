`timescale 1ns/1ps
module tb_core;
reg clk=0;always #3.5 clk=~clk;
reg rst=0,start=0,ce=1,we=0;reg[5:0] addr=0;reg[63:0] data=0;
wire done,ready,v1,v2,v3;wire[7:0]o1,o2,o2b,o2c,o2d,o3;wire[6:0]a1;wire[4:0]a2;wire a3;
lab7_core dut(.clk_i(clk),.rst_n_i(rst),.start_i(start),.ce_i(ce),.load_we_i(we),.load_addr_i(addr),.load_data_i(data),.done_o(done),.ready_o(ready),.fc1_wren_o(v1),.fc1_data_o(o1),.fc1_addr_o(a1),.fc2_wren_o(v2),.fc2_data_o(o2),.fc2_data_b_o(o2b),.fc2_data_c_o(o2c),.fc2_data_d_o(o2d),.fc2_addr_o(a2),.fc3_wren_o(v3),.fc3_data_o(o3),.fc3_addr_o(a3));
reg[7:0] xs[0:24575],gold[0:7775];integer si,s,j,k,n1,n2,n3,cycles,checked=0,minimum=99999,maximum=0;
initial begin
$readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/inputs.mem",xs);$readmemh("/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/data/features.mem",gold);
repeat(32)@(negedge clk);rst=1;
for(si=0;si<8;si=si+1)begin s=(si==7)?47:si*7;
for(j=0;j<64;j=j+1)begin @(negedge clk);we=1;addr=j;for(k=0;k<8;k=k+1)data[k*8+:8]=xs[s*512+j*8+k];end
@(negedge clk);we=0;start=1;@(negedge clk);start=0;n1=0;n2=0;n3=0;cycles=0;
while(!done)begin
@(posedge clk);#1;cycles=cycles+1;
if(v1)begin if(s==0 && a1==127)$display("EVENT FC1_LAST %0d",cycles);if(a1!==n1 || o1!==gold[s*162+n1])$fatal(1,"FC1 s=%0d n=%0d got=%h expected=%h addr=%0d",s,n1,o1,gold[s*162+n1],a1);n1=n1+1;checked=checked+1;end
if(v2)begin if(s==0 && a2==28)$display("EVENT FC2_LAST %0d",cycles);if(a2!==n2 || {o2d,o2c,o2b,o2}!=={gold[s*162+128+n2+3],gold[s*162+128+n2+2],gold[s*162+128+n2+1],gold[s*162+128+n2]})$fatal(1,"FC2 s=%0d n=%0d",s,n2);n2=n2+4;checked=checked+4;end
if(v3)begin if(s==0 && a3==1)$display("EVENT FC3_LAST %0d",cycles);if(a3!==n3%2 || o3!==gold[s*162+160+n3])$fatal(1,"FC3 s=%0d n=%0d",s,n3);n3=n3+1;checked=checked+1;end
if(cycles>1000)$fatal(1,"timeout");@(negedge clk);
end
if(n1!=128 || n2!=32 || n3!=2)$fatal(1,"counts");
if(cycles<minimum)minimum=cycles;if(cycles>maximum)maximum=cycles;repeat(8)@(negedge clk);
end
$display("PASS CORE samples=8 values=%0d start_to_done_cycles=%0d..%0d",checked,minimum,maximum);$finish;
end
initial begin #3000000;$fatal(1,"watchdog");end
endmodule
