from pathlib import Path
import json
r=Path('/home/ding/vivado_project/Lab5_optimization');rows=(r/'data/stream_pair256_hybrid_weights.mem').read_text().split();bias=[int(x,16) for x in (r/'data/fc1_paired_bias.mem').read_text().split()]
lo=[];hi=[];prefix_checks=0
sign=lambda n:n-256 if n>=128 else n
for pair in range(64):
 for half in range(2):
  ws=[]
  for group in range(2):
   word=int(rows[pair*2+group],16)
   for lane in range(256):ws.append(sign((word>>((255-lane)*16+half*8))&255))
  b=sign((bias[pair]>>(half*8))&255);lower=upper=b
  for w in ws:
   lower+=w*(-128 if w>=0 else 127);upper+=w*(127 if w>=0 else -128)
   assert -(1<<22)<=lower<=upper<(1<<22)
   prefix_checks+=1
  for group in range(2):
   gl=sum(w*(-128 if w>=0 else 127) for w in ws[group*256:(group+1)*256]);gu=sum(w*(127 if w>=0 else -128) for w in ws[group*256:(group+1)*256])
   assert -(1<<22)<=gl<=gu<(1<<22)
  lo.append(lower);hi.append(upper)
f=r/'data/bounds.json';v=json.loads(f.read_text());v['fc1_lower']=lo;f.write_text(json.dumps(v,indent=2))
(r/'results/fc1_width_proof.txt').write_text(f'PASS: all {prefix_checks} FC1 accumulation prefixes and all 256 group sums fit signed 23 bits for every signed 8-bit input.\nFixed supplied weights: minimum {min(lo)}, maximum {max(hi)}.\n')
print(min(lo),max(hi))
