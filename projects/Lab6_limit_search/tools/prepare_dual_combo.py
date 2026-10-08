from pathlib import Path
import shutil,json
R=Path('/home/ding/vivado_project/Lab6_limit_search');src=R/'dual512_full_lookup';d=R/'dual512_hybrid_full_lookup'
for sub in ['rtl','data','tb','tools']:
 shutil.copytree(src/sub,d/sub,dirs_exist_ok=True)
 for p in (d/sub).glob('*'):
  if p.suffix in ['.v','.tcl']:p.write_text(p.read_text().replace(str(src),str(d)).replace(src.name,d.name))
(d/'results').mkdir(exist_ok=True);shutil.copy2(src/'timing.xdc',d/'timing.xdc');shutil.copy2(R/'dual512_hybrid/rtl/adder_tree.v',d/'rtl/adder_tree.v');shutil.copy2(R/'dual512_hybrid/data/tree_width_proof.json',d/'data/tree_width_proof.json')
p=d/'rtl/fc1_paired.v';s=p.read_text().replace('[16:0] valid_pipe','[15:0] valid_pipe').replace('tag[0:16]','tag[0:15]').replace('tag[16]','tag[15]').replace('valid_pipe[16]','valid_pipe[15]').replace('valid_pipe[15:0]','valid_pipe[14:0]').replace('j<17','j<16');p.write_text(s)
c=json.loads((src/'config.json').read_text());c.update(name=d.name,source=str(src),cycles=106,tree_stages=8);c['options']['radices']=[3,3,2,2,2,2,2,2];(d/'config.json').write_text(json.dumps(c,indent=2));p=R/'results/plan.json';c=json.loads(p.read_text());c['candidates'].append(d.name);p.write_text(json.dumps(c,indent=2))
