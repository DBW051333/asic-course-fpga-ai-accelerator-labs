from pathlib import Path
import shutil,json
R=Path('/home/ding/vivado_project/Lab6_limit_search');src=R/'dual512_lookup';d=R/'dual512_full_lookup'
for sub in ['rtl','data','tb','tools']:
 shutil.copytree(src/sub,d/sub,dirs_exist_ok=True)
 for p in (d/sub).glob('*'):
  if p.suffix in ['.v','.tcl']:p.write_text(p.read_text().replace(str(src),str(d)).replace(src.name,d.name))
(d/'results').mkdir(exist_ok=True);shutil.copy2(src/'timing.xdc',d/'timing.xdc')
p=d/'rtl/fc1_paired.v';s=p.read_text().replace(' integer sn,un;', ''' (* rom_style="distributed" *) reg [7:0] nibble_uu[0:255];
 (* rom_style="distributed" *) reg signed [7:0] nibble_ss[0:255];
 integer aa,bb;
 initial begin
  for(aa=0;aa<16;aa=aa+1)for(bb=0;bb<16;bb=bb+1)begin
   nibble_uu[aa*16+bb]=aa*bb;
   nibble_ss[aa*16+bb]=(aa<8?aa:aa-16)*(bb<8?bb:bb-16);
  end
 end
 integer sn,un;''').replace('pp00<=input_p[g][3:0]*w[3:0];','pp00<=nibble_uu[{input_p[g][3:0],w[3:0]}];').replace('pp11<=$signed(input_p[g][7:4])*$signed(w[7:4]);','pp11<=nibble_ss[{input_p[g][7:4],w[7:4]}];');p.write_text(s)
c=json.loads((src/'config.json').read_text());c.update(name=d.name,source=str(src));c['options']['all_nibble_products_lookup']=True;(d/'config.json').write_text(json.dumps(c,indent=2));p=R/'results/plan.json';c=json.loads(p.read_text());c['candidates'].append(d.name);p.write_text(json.dumps(c,indent=2))
