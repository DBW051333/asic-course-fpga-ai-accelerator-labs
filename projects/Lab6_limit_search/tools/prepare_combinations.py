from pathlib import Path
import json,shutil
ROOT=Path('/home/ding/vivado_project/Lab6_limit_search');src=ROOT/'fc1_prepack_pipe_narrow'
p=ROOT/'results/plan.json';plan=json.loads(p.read_text())
for name,tree in [('prepack_ternary_bias','ternary6_bias_narrow'),('prepack_hybrid_bias','hybrid7_bias_narrow')]:
 td=ROOT/tree;tc=json.loads((td/'config.json').read_text());levels=tc['tree_stages'];last=7+levels
 d=ROOT/name;d.mkdir(exist_ok=True)
 for sub in ['rtl','data','tb','tools']:
  shutil.copytree(src/sub,d/sub,dirs_exist_ok=True)
  for f in (d/sub).glob('*'):
   if f.suffix in ['.v','.tcl']:f.write_text(f.read_text().replace(str(src),str(d)).replace(src.name,name))
 (d/'results').mkdir(exist_ok=True);shutil.copy2(src/'timing.xdc',d/'timing.xdc');shutil.copy2(td/'rtl/adder_tree.v',d/'rtl/adder_tree.v');shutil.copy2(td/'data/tree_width_proof.json',d/'data/tree_width_proof.json')
 f=d/'rtl/fc1_paired.v';s=f.read_text().replace('[15:0] valid_pipe',f'[{last}:0] valid_pipe').replace('tag[0:15]',f'tag[0:{last}]').replace('tag[15]',f'tag[{last}]').replace('valid_pipe[15]',f'valid_pipe[{last}]').replace('valid_pipe[14:0]',f'valid_pipe[{last-1}:0]').replace('j<16',f'j<{last+1}')
 s=s.replace(f'wire [15:0] bias_pair=biases[tag[{last}][7:2]];',f'reg [15:0] bias_pipe[0:{last}];\n wire [15:0] bias_pair=bias_pipe[{last}];').replace('integer j;','integer j,bi;')
 s=s.replace('weight_r<=weights[issue_addr];',f'bias_pipe[0]<=biases[issue_pair];\n  for(bi=1;bi<{last+1};bi=bi+1)bias_pipe[bi]<=bias_pipe[bi-1];\n  weight_r<=weights[issue_addr];');f.write_text(s)
 cfg=json.loads((src/'config.json').read_text());cfg.update(name=name,source=str(src),cycles=170+levels-8,tree_stages=levels);cfg['options'].update(bias_pipeline=True,radices=tc['options']['radices']);(d/'config.json').write_text(json.dumps(cfg,indent=2));plan['candidates'].append(name)
p.write_text(json.dumps(plan,indent=2));print('Prepared two exact combinations of prepacked ROM, early bias and reduced-depth trees')
