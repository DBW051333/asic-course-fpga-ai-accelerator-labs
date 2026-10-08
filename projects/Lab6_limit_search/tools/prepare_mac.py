from pathlib import Path
import json,shutil,sys
ROOT=Path('/home/ding/vivado_project/Lab6_limit_search')
src=ROOT/'free_address_pipe_narrow';d=ROOT/'dsp_packed_mac_narrow';d.mkdir(exist_ok=True)
for sub in ['rtl','tb','tools','data']:
 shutil.copytree(src/sub,d/sub,dirs_exist_ok=True)
 for p in (d/sub).glob('*'):
  if p.suffix in ['.v','.tcl']:p.write_text(p.read_text().replace(str(src),str(d)).replace(src.name,d.name))
(d/'results').mkdir(exist_ok=True);shutil.copy2(src/'timing.xdc',d/'timing.xdc')
cfg=json.loads((src/'config.json').read_text());cfg.update(name=d.name,source=str(src));cfg['options']['packed_mac']=True
(d/'config.json').write_text(json.dumps(cfg,indent=2))
p=ROOT/'results/plan.json';cfg=json.loads(p.read_text());cfg['candidates'].append(d.name);p.write_text(json.dumps(cfg,indent=2))
# For all signed INT8 products, recover each low-channel accumulation quotient
# from modulo-65536 wrap and the signed product direction. No product truncation.
sys.path.insert(0,'/home/ding/vivado_project/Lab5_truncation_optimization/tools')
from search_quantization import W,B
import numpy as np
rng=np.random.default_rng(20261005);X=rng.integers(-128,128,size=(4096,128),dtype=np.int64)
X=np.vstack([X,np.full((1,128),-128),np.full((1,128),127),np.zeros((1,128),dtype=np.int64)])
checks=0
for g in range(16):
 w0=W[1][:,2*g];w1=W[1][:,2*g+1];b0=int(B[1][2*g]);b1=int(B[1][2*g+1])
 packed=np.full(len(X),(b1<<16)+b0,dtype=np.int64);exact0=np.full(len(X),b0,dtype=np.int64);exact1=np.full(len(X),b1,dtype=np.int64);q=np.zeros(len(X),dtype=np.int64);old=np.zeros(len(X),dtype=np.int64)
 for i in range(128):
  p0=X[:,i]*w0[i];p1=X[:,i]*w1[i];packed+=(p1<<16)+p0;exact0+=p0;exact1+=p1;low=packed&65535
  if i==0:q=np.where(low>=32768,-1,0)
  else:q+=np.where((p0<0)&(low>old),-1,np.where((p0>=0)&(low<old),1,0))
  assert np.array_equal((q<<16)+low,exact0)
  assert np.array_equal((packed>>16)-q,exact1)
  old=low;checks+=len(X)*2
(ROOT/'results/packed_mac_math_proof.json').write_text(json.dumps(dict(status='passed',checks=checks,vectors=len(X),pairs=16,prefixes=128,formula='S0 = (q << 16) + unsigned_low16; S1 = signed_packed_sum >> 16 - q',scope='Every prefix of seeded random and boundary vectors for fixed FC2 weights; algebraic derivation plus tests, not exhaustive input-vector enumeration'),indent=2))
print('Prepared packed MAC candidate; checked',checks,'prefix recoveries')
