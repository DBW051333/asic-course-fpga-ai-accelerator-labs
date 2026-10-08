from pathlib import Path
import json,shutil
R=Path('/home/ding/vivado_project/Lab6_limit_search');src=R/'dsp_mac_pipe_bias';d=R/'dsp_mac_lookup_cross'
for sub in ['rtl','data','tb','tools']:
 shutil.copytree(src/sub,d/sub,dirs_exist_ok=True)
 for p in (d/sub).glob('*'):
  if p.suffix in ['.v','.tcl']:p.write_text(p.read_text().replace(str(src),str(d)).replace(src.name,d.name))
(d/'results').mkdir(exist_ok=True);shutil.copy2(src/'timing.xdc',d/'timing.xdc')
p=d/'rtl/fc1_paired.v';s=p.read_text();s=s.replace('integer j,bi;', '''integer j,bi;
 (* rom_style="distributed" *) reg signed [7:0] nibble_su[0:255];
 integer sn,un;
 initial begin
  for(sn=0;sn<16;sn=sn+1)
   for(un=0;un<16;un=un+1)nibble_su[sn*16+un]=(sn<8?sn:sn-16)*un;
 end''')
s=s.replace("pp01<=$signed(input_p[g][7:4])*$signed({1'b0,w[3:0]});",'pp01<=nibble_su[{input_p[g][7:4],w[3:0]}];').replace("pp10<=$signed({1'b0,input_p[g][3:0]})*$signed(w[7:4]);",'pp10<=nibble_su[{w[7:4],input_p[g][3:0]}];');p.write_text(s)
c=json.loads((src/'config.json').read_text());c.update(name=d.name,source=str(src));c['options']['lookup_cross_products']=True;(d/'config.json').write_text(json.dumps(c,indent=2))
p=R/'results/plan.json';c=json.loads(p.read_text());c['candidates'].append(d.name);p.write_text(json.dumps(c,indent=2))
print('Prepared exact nibble lookup replacement')
