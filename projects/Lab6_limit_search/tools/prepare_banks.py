from pathlib import Path
import json,shutil
R=Path('/home/ding/vivado_project/Lab6_limit_search');src=R/'fc1_prepack_pipe_narrow';d=R/'prepack_address_banks'
for sub in ['rtl','data','tb','tools']:
 shutil.copytree(src/sub,d/sub,dirs_exist_ok=True)
 for p in (d/sub).glob('*'):
  if p.suffix in ['.v','.tcl']:p.write_text(p.read_text().replace(str(src),str(d)).replace(src.name,d.name))
(d/'results').mkdir(exist_ok=True);shutil.copy2(src/'timing.xdc',d/'timing.xdc')
p=d/'rtl/fc1_paired.v';s=p.read_text();s=s.replace(' genvar g;generate', ''' genvar bank;generate for(bank=0;bank<LANES/16;bank=bank+1)begin:address_bank
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-bank*400 -:400]<=weights[local_addr][LANES*25-1-bank*400 -:400];
 end
 end endgenerate
 genvar g;generate''');s=s.replace('weight_r<=weights[issue_addr];','');p.write_text(s)
c=json.loads((src/'config.json').read_text());c.update(name=d.name,source=str(src));c['options']['independent_address_banks']=16;(d/'config.json').write_text(json.dumps(c,indent=2));p=R/'results/plan.json';c=json.loads(p.read_text());c['candidates'].append(d.name);p.write_text(json.dumps(c,indent=2))
