from pathlib import Path
import ast,shutil
r=Path('/home/ding/vivado_project/Lab5_optimization');src=r/'stream_pair256_quadtail_clk5';d=r/'stream_pair256_quad_tree7_clk4p8'
for n in ['rtl','tb','tools']:shutil.copytree(src/n,d/n,dirs_exist_ok=True)
(d/'results').mkdir(exist_ok=True)
p=d/'rtl/fc1_paired.v';s=p.read_text().replace('reg [11:0] valid_pipe;reg [7:0] tag[0:11]','reg [13:0] valid_pipe;reg [7:0] tag[0:13]').replace('tag[11]','tag[13]').replace('valid_pipe[10:0]','valid_pipe[12:0]').replace('j<12','j<14').replace('valid_pipe[11])','valid_pipe[13])');p.write_text(s)
a=ast.parse((r/'tools/build_variants.py').read_text());fn=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='tree');ctx={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'tree','exec'),ctx)
(d/'rtl/adder_tree.v').write_text(ctx['tree'](256,[2,1,1,1,1,1,1]))
for p in (d/'tools').glob('*.tcl'):
 s=p.read_text().replace(str(src),str(d)).replace(src.name+'.xpr',d.name+'.xpr').replace('create_project '+src.name,'create_project '+d.name).replace('-period 5.000','-period 4.800');p.write_text(s)
print(d)
