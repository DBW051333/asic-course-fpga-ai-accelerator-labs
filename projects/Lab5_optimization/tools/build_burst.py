from pathlib import Path
import shutil
r=Path('/home/ding/vivado_project/Lab5_optimization');src=r/'stream_pair256_quad_tree7_clk4p8';d=r/'stream_pair256_burst_tree7_clk4p8'
for n in ['rtl','tb','tools']:shutil.copytree(src/n,d/n,dirs_exist_ok=True)
(d/'results').mkdir(exist_ok=True)
p=d/'rtl/fc1_paired.v';s=p.read_text().replace('input wire clk_i,rst_n_i,start_i,output reg done_o,','input wire clk_i,rst_n_i,start_i,output wire ready_o,output reg done_o,').replace('reg running;','reg running;\n assign ready_o=rst_n_i && !running;');p.write_text(s)
p=d/'rtl/fc_stream_pair_output.v';s=p.read_text().replace('reg signed [AW-1:0] acc [0:NO-1];','reg signed [AW-1:0] acc [0:NO-1], snapshot [0:NO-1];')
s=s.replace('                end\n                if(last_pipe[3])', '''                    if(last_pipe[3]) snapshot[j] <= acc[j]+{{(AW-PW){product_r[j][PW-1]}},product_r[j]};
                end
                if(last_pipe[3])''').replace('<=acc[emit_idx','<=snapshot[emit_idx');p.write_text(s)
p=d/'rtl/lab5_top.v';s=p.read_text().replace('output wire done_o,','output wire done_o,ready_o,').replace('.done_o(d1),','.done_o(d1),.ready_o(ready_o),');p.write_text(s)
p=d/'rtl/lab5_impl_top.v';s=p.read_text().replace('output wire done_o,','output wire done_o,ready_o,').replace('.done_o(done_o),','.done_o(done_o),.ready_o(ready_o),');p.write_text(s)
s=(d/'tb/tb_lab5_validation.v').read_text().replace('module tb_lab5_validation;','module tb_lab5_burst;').replace('ref1[0:127],ref2[0:31],ref3[0:1]','ref1[0:767],ref2[0:191],ref3[0:11]').replace('ref1[i]','ref1[job*128+i]').replace('ref2[i]','ref2[job*32+i]').replace('ref3[i]','ref3[job*2+i]')
a=s.index('initial begin');b=s.index('  $readmemh(',a)
refloads=s[s.index('  f=$fopen',a):b]
s=s[:a]+'''realtime launched_jobs[0:5];integer completed=0;
initial begin
 for(job=0;job<6;job=job+1)begin
'''+refloads+''' end
 repeat(5) @(negedge clk_i);rst_n_i=1;
 for(job=0;job<6;job=job+1)begin
  wait(dut.ready_o);@(negedge clk_i);
'''+s[b:]
s=s.replace('  n1=0;n2=0;n3=0;start_i=1;launched=$time+5;','  start_i=1;launched=$time+5;launched_jobs[job]=launched;')
a=s.index('  @(posedge done_o);');b=s.index(' if(errors==0)',a)
s=s[:a]+''' end
 wait(completed==6);repeat(3)@(negedge clk_i);
 if(n1!=768 || n2!=192 || n3!=12)begin errors=errors+1;$display("COUNT_FAIL %d %d %d",n1,n2,n3);end
'''+s[b:]
s=s.replace('PASS: six different consecutive networks, all 972 values and addresses match','PASS: six overlapping different networks, all 972 values and addresses match').replace('a1!==n1','a1!==(n1%128)').replace('a2!==n2','a2!==(n2%32)').replace('a3!==n3','a3!==(n3%2)')
s=s.replace('always @(posedge clk_i) begin','''always @(posedge done_o)begin
 $display("BURST job=%0d latency_ns=%0.3f launch_ns=%0.3f finish_ns=%0.3f",completed,$realtime-launched_jobs[completed],launched_jobs[completed],$realtime);
 completed=completed+1;
end
always @(posedge clk_i) begin''')
(d/'tb/tb_lab5_burst.v').write_text(s)
for p in (d/'tools').glob('*.tcl'):
 s=p.read_text().replace(str(src),str(d)).replace(src.name+'.xpr',d.name+'.xpr').replace('create_project '+src.name,'create_project '+d.name);p.write_text(s)
s=(d/'tools/run_final_validation.tcl').read_text().replace('tb_lab5_validation','tb_lab5_burst')
(d/'tools/run_burst.tcl').write_text(s)
print(d)
