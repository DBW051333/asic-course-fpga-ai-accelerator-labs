from pathlib import Path
import json,shutil
R=Path('/home/ding/vivado_project/Lab6_limit_search');src=R/'prepack_address_banks';d=R/'prepack_banked_rom'
for sub in ['rtl','data','tb','tools']:
 shutil.copytree(src/sub,d/sub,dirs_exist_ok=True)
 for p in (d/sub).glob('*'):
  if p.suffix in ['.v','.tcl']:p.write_text(p.read_text().replace(str(src),str(d)).replace(src.name,d.name))
(d/'results').mkdir(exist_ok=True);shutil.copy2(src/'timing.xdc',d/'timing.xdc')
rows=(d/'data/fc1_prepacked.mem').read_text().splitlines()
for b in range(16):(d/f'data/fc1_bank{b}.mem').write_text('\n'.join(r[b*100:(b+1)*100] for r in rows)+'\n')
p=d/'rtl/fc1_paired.v';s=p.read_text().replace(' (* rom_style="block" *) reg [LANES*25-1:0] weights[0:64*GROUPS-1];','').replace('$readmemh(WEIGHTS,weights);','')
a=s.index(' genvar bank;generate');z=s.index(' genvar g;generate',a)
blocks=[]
for b in range(16):
 blocks.append(f''' generate if(LANES/16>{b})begin:address_bank{b}
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("{d}/data/fc1_bank{b}.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
  local_addr<=local_addr+1'b1;
  if(!rst_n_i || (start_i && !running))local_addr<=0;
  weight_r[LANES*25-1-{b}*400 -:400]<=local_weights[local_addr];
 end
 end endgenerate\n''')
s=s[:a]+''.join(blocks)+s[z:];p.write_text(s)
c=json.loads((src/'config.json').read_text());c.update(name=d.name,source=str(src));c['options']['explicit_banked_rom']=True;(d/'config.json').write_text(json.dumps(c,indent=2));p=R/'results/plan.json';c=json.loads(p.read_text());c['candidates'].append(d.name);p.write_text(json.dumps(c,indent=2))
