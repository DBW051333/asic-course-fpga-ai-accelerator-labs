"""Recompute all 48 samples from original course weights with scalar integers."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
def signed(x):return (x+128)%256-128
def coe(p):
 text=p.read_text().split('memory_initialization_vector',1)[1].split('=',1)[1]
 return [signed(int(t.strip(),2)) for t in text.replace(';','').split(',') if t.strip()]
xs=[signed(int(t,16)) for t in (R/'data/inputs.mem').read_text().split()]
gold=[signed(int(t,16)) for t in (R/'data/features.mem').read_text().split()]
pred=[int(t,16) for t in (R/'data/predictions.mem').read_text().split()]
labels=[int(t,16) for t in (R/'data/labels.mem').read_text().split()]
weights=[coe(R/'data/model'/n) for n in ['fc1.0.weight.coe','fc2.0.weight.coe','fc3.weight.coe']]
biases=[coe(R/'data/model'/n) for n in ['fc1.0.bias.coe','fc2.0.bias.coe','fc3.bias.coe']]
computed=[];preds=[]
for j in range(48):
 x=xs[j*512:(j+1)*512];fs=[]
 for w,b,n,sh,relu in zip(weights,biases,[128,32,2],[10,9,8],[True,True,False]):
  out=[]
  for k in range(n):
   acc=b[k]
   for i,a in enumerate(x):acc+=a*w[k*len(x)+i]
   if relu:acc=max(0,acc)
   out.append(signed(acc>>sh))
  x=out;fs+=out
 computed+=fs;preds.append(int(x[0]<x[1]))
assert computed==gold and preds==pred
ranges=[]
for o,n in [(0,128),(128,32),(160,2)]:
 per=[{'sample':j+1,'min':min(computed[j*162+o:j*162+o+n]),'max':max(computed[j*162+o:j*162+o+n])} for j in range(42)]
 lo=min(v['min'] for v in per);hi=max(v['max'] for v in per)
 ranges.append({'course_min':lo,'course_max':hi,'aggregate_amplitude_requirement_pass':63<hi<127 or -128<lo<-64,
                'per_sample_amplitude_requirement_pass_count':sum(63<v['max']<127 or -128<v['min']<-64 for v in per),'per_sample':per})
result={'pass':True,'samples':48,'values':len(computed),'mismatches':0,'course_correct':sum(a==b for a,b in zip(preds[:42],labels)),
        'layer_ranges':ranges,'amplitude_interpretation':'Aggregate course extrema satisfy the PPT range; the stricter every-sample interpretation is not satisfied by the unchanged fixed-shift Lab7 baseline.',
        'model_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'data/model').glob('*.coe')}}
(R/'results/reference_verified.json').write_text(json.dumps(result,indent=2));print(f"PASS independent scalar reference: 48 samples, 7776 values, correct {result['course_correct']}/42")
print('Per-sample amplitude pass counts:',[v['per_sample_amplitude_requirement_pass_count'] for v in ranges])
