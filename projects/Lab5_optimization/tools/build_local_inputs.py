from pathlib import Path
import shutil
r=Path('/home/ding/vivado_project/Lab5_optimization');src=r/'stream_pair256_banked_exact23_tree7_clk4p8';d=r/'stream_pair256_localinput_exact23_tree7_clk4p8'
for n in ['rtl','tb','tools']:shutil.copytree(src/n,d/n,dirs_exist_ok=True)
(d/'results').mkdir(exist_ok=True)
p=d/'rtl/fc1_paired.v';s=p.read_text();a=s.index('  end else begin\n   wire signed [15:0] result');b=s.index('   assign product[g]={result[1]',a)
part=s[a:b].replace('input_p[g]','local_input')
part=part.replace('   wire signed [15:0] result[0:1];','''   wire signed [15:0] result[0:1];
   // Preserve one local input register per fabric lane to avoid merged broadcast drivers.
   (* keep="true",dont_touch="true" *) reg signed [7:0] local_input;
   always @(posedge clk_i) local_input<=input_rd[LANES*8-1-g*8 -:8];''')
s=s[:a]+part+s[b:];p.write_text(s)
for p in (d/'tools').glob('*.tcl'):
 s=p.read_text().replace(str(src),str(d)).replace(src.name+'.xpr',d.name+'.xpr').replace('create_project '+src.name,'create_project '+d.name);p.write_text(s)
print(d)
