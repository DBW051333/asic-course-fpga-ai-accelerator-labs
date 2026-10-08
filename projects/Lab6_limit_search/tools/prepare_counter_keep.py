from pathlib import Path
import json,shutil
R=Path('/home/ding/vivado_project/Lab6_limit_search');src=R/'fc1_prepack_pipe_narrow';d=R/'prepack_counter_keep'
for sub in ['rtl','data','tb','tools']:
 shutil.copytree(src/sub,d/sub,dirs_exist_ok=True)
 for p in (d/sub).glob('*'):
  if p.suffix in ['.v','.tcl']:p.write_text(p.read_text().replace(str(src),str(d)).replace(src.name,d.name))
(d/'results').mkdir(exist_ok=True);shutil.copy2(src/'timing.xdc',d/'timing.xdc')
p=d/'rtl/fc1_paired.v';s=p.read_text().replace('reg [$clog2(64*GROUPS)-1:0] issue_addr;', '(* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] issue_addr;');p.write_text(s)
c=json.loads((src/'config.json').read_text());c.update(name=d.name,source=str(src));c['options']['preserve_central_address_register']=True;(d/'config.json').write_text(json.dumps(c,indent=2));p=R/'results/plan.json';c=json.loads(p.read_text());c['candidates'].append(d.name);p.write_text(json.dumps(c,indent=2))
