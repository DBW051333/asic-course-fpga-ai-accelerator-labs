from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;D=R/'hybrid256/data';B=R/'baseline192/data';M=(1<<25)-1
def signed(v,n):return v-(1<<n) if v&(1<<(n-1)) else v
def banks(root,n):return [[int(v,16) for v in (root/f'fc1_bank{i}.mem').read_text().split()] for i in range(n)]
def lane(bb,row,i):return (bb[i//16][row]>>((15-i%16)*25))&M
a=banks(B,12);c=banks(D,16);minimum=0;maximum=0;checked=0
for row in range(145):
 for i in range(256):
  v=lane(c,row,i);sv=signed(v,25)
  assert -8388608<=sv<=8388607,('signed24 domain',row,i,sv)
  assert ((v>>8)&255)==(255 if v&128 else 0),('packed sign structure',row,i)
  if row<128:
   p,g=divmod(row,2);n=g*256+i;old=lane(a,p*3+n//192,n%192)
  else:old=lane(a,192+row-128,i) if i<192 else 0
  assert v==old,('coefficient changed',row,i)
  minimum=min(minimum,sv);maximum=max(maximum,sv);checked+=1
for n in ['shared_bias.mem','inputs.mem','features.mem','predictions.mem','labels.mem','fc2_packed_weights.mem','fc3_packed_weights.mem']:
 assert (D/n).read_bytes()==(B/n).read_bytes(),n
s={'pass':True,'packed_words_checked':checked,'packed_min':minimum,'packed_max':maximum,'signed24_legal':True,'fixed_packed_structure_legal':True,'all_three_layers_exactly_repacked_from_frozen_parent':True,'biases_inputs_golden_outputs_unchanged':True,'weight_bank_sha256':{f'fc1_bank{i}.mem':hashlib.sha256((D/f'fc1_bank{i}.mem').read_bytes()).hexdigest() for i in range(16)}}
(R/'hybrid256/results/model_verification.json').write_text(json.dumps(s,indent=2));print('PASS exact fixed-model repacking and signed24 guard:',checked,'packed words')
