from pathlib import Path
import re,random,json
r=Path('/home/ding/vivado_project/Lab5_optimization');d=Path('/home/ding/vivado_project/Lab5/data/params')
def vals(p):
 s=p.read_text().split('memory_initialization_vector')[1].split('=',1)[1]
 return [int(x,2)-(256 if x[0]=='1' else 0) for x in re.findall('[01]{8}',s)]
w1,w2,w3=[vals(d/n) for n in ('fc1.0.weight.coe','fc2.0.weight.coe','fc3.weight.coe')]
b1,b2,b3=[vals(d/n) for n in ('fc1.0.bias.coe','fc2.0.bias.coe','fc3.bias.coe')]
x0=vals(Path('/home/ding/vivado_project/Lab5/data/input/sel_data_128.coe'))
def fc(x,w,b,ni,relu):
 return [max(0,t) if relu else t for o in range(len(b)) for t in [b[o]+sum(a*v for a,v in zip(w[o*ni:(o+1)*ni],x))]]
rng=random.Random(20261005);row=max(range(128),key=lambda o:sum(abs(z) for z in w1[o*512:(o+1)*512]))
vecs=[('course',x0),('negative_limit',[-128]*512),('positive_limit',[127]*512),('alternating',[-128 if i%2 else 127 for i in range(512)]),('random',[rng.randrange(-128,128) for _ in range(512)]),('fc1_extremum',[127 if z>=0 else -128 for z in w1[row*512:(row+1)*512]])]
out=r/'data/validation';out.mkdir(exist_ok=True);manifest=[]
for i,(name,x) in enumerate(vecs):
 a=fc(x,w1,b1,512,True);b=fc(a,w2,b2,128,True);c=fc(b,w3,b3,32,False)
 if i==0:
  for n,y in [(1,a),(2,b),(3,c)]:assert y==[int(z) for z in Path(f'/home/ding/vivado_project/Lab5/data/reference/fc{n}.txt').read_text().split()]
 (out/f'input{i}.mem').write_text('\n'.join(f'{z&255:02x}' for z in x)+'\n')
 for n,y in [(1,a),(2,b),(3,c)]:(out/f'case{i}_fc{n}.txt').write_text('\n'.join(str(z) for z in y)+'\n')
 manifest.append(dict(case=i,name=name,fc1_max=max(a),fc2_max=max(b),fc3=c))
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(manifest)
