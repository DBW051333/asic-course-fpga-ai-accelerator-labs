from pathlib import Path
import ast,shutil
r=Path('/home/ding/vivado_project/Lab5_optimization');src=r/'stream_pair256_staged'
a=ast.parse((r/'tools/build_variants.py').read_text());fn=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='tree');ctx={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'tree','exec'),ctx)
for name,parts in [('stream_pair256_five_clk5',[2,2,2,1,1]),('stream_pair256_3221_clk5',[3,2,2,1])]:
 d=r/name
 for f in ('rtl','tb','tools'):shutil.copytree(src/f,d/f,dirs_exist_ok=True)
 (d/'results').mkdir(exist_ok=True)
 (d/'rtl/adder_tree.v').write_text(ctx['tree'](256,parts))
 if len(parts)==5:
  p=d/'rtl/fc1_paired.v';s=p.read_text().replace('reg [8:0] valid_pipe;reg [7:0] tag[0:8]','reg [9:0] valid_pipe;reg [7:0] tag[0:9]').replace('tag[8]','tag[9]').replace('valid_pipe[7:0]','valid_pipe[8:0]').replace('j<9','j<10').replace('valid_pipe[8])','valid_pipe[9])');p.write_text(s)
 for p in (d/'tools').glob('*.tcl'):
  s=p.read_text().replace(str(src),str(d)).replace('create_project stream_pair256_staged','create_project '+name).replace('/vivado/stream_pair256_staged.xpr','/vivado/'+name+'.xpr').replace('-period 10.000','-period 5.000');p.write_text(s)
 print(name)
