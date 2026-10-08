from pathlib import Path
import shutil,json
R=Path('/home/ding/vivado_project/Lab6_limit_search');src=R/'prepack_banked_rom';d=R/'prepack_banked_bias'
for sub in ['rtl','data','tb','tools']:
 shutil.copytree(src/sub,d/sub,dirs_exist_ok=True)
 for p in (d/sub).glob('*'):
  if p.suffix in ['.v','.tcl']:p.write_text(p.read_text().replace(str(src),str(d)).replace(src.name,d.name))
(d/'results').mkdir(exist_ok=True);shutil.copy2(src/'timing.xdc',d/'timing.xdc')
p=d/'rtl/fc1_paired.v';s=p.read_text().replace('wire [15:0] bias_pair=biases[tag[15][7:2]];', 'reg [15:0] bias_pipe[0:15];\n wire [15:0] bias_pair=bias_pipe[15];').replace('integer j;','integer j,bi;').replace('  issue_addr<=issue_addr+1\'b1;', '  issue_addr<=issue_addr+1\'b1;\n  bias_pipe[0]<=biases[issue_pair];\n  for(bi=1;bi<16;bi=bi+1)bias_pipe[bi]<=bias_pipe[bi-1];');p.write_text(s)
c=json.loads((src/'config.json').read_text());c.update(name=d.name,source=str(src));c['options']['bias_pipeline']=True;(d/'config.json').write_text(json.dumps(c,indent=2));p=R/'results/plan.json';c=json.loads(p.read_text());c['candidates'].append(d.name);p.write_text(json.dumps(c,indent=2))
