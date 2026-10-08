from pathlib import Path
import shutil
r=Path('/home/ding/vivado_project/Lab5_optimization');src=r/'stream_pair256_burst_tree7_clk4p8';d=r/'stream_pair256_burst_exact23_tree7_clk4p8'
for n in ['rtl','tb','tools']:shutil.copytree(src/n,d/n,dirs_exist_ok=True)
(d/'results').mkdir(exist_ok=True)
p=d/'rtl/fc1_paired.v';s=p.read_text().replace('reg [15:0] biases[0:63];','(* rom_style="distributed" *) reg [15:0] biases[0:63];').replace('reg signed [31:0] acc0,acc1,pair0,pair1','reg signed [22:0] acc0,acc1,pair0,pair1')
s=s.replace('wire signed [31:0] b0={{24','wire signed [22:0] b0={{15').replace('wire signed [31:0] b1={{24','wire signed [22:0] b1={{15')
s=s.replace('integer j;', 'wire signed [22:0] group_sum0=sum0[22:0],group_sum1=sum1[22:0];\n integer j;').replace('<=sum0+b0','<=group_sum0+b0').replace('<=sum1+b1','<=group_sum1+b1').replace('<=acc0+sum0','<=acc0+group_sum0').replace('<=acc1+sum1','<=acc1+group_sum1')
s=s.replace("pair0[31]?32'd0:pair0","pair0[22]?32'd0:{{9{pair0[22]}},pair0}").replace("pair1[31]?32'd0:pair1","pair1[22]?32'd0:{{9{pair1[22]}},pair1}");p.write_text(s)
for p in (d/'tools').glob('*.tcl'):
 s=p.read_text().replace(str(src),str(d)).replace(src.name+'.xpr',d.name+'.xpr').replace('create_project '+src.name,'create_project '+d.name);p.write_text(s)
print(d)
