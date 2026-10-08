from pathlib import Path
import numpy as np,json,re
R=Path('/home/ding/vivado_project/Lab6_architecture_trials');D=Path('/home/ding/vivado_project/Lab6/data')
def coe(p):
 body=p.read_text().split('memory_initialization_vector',1)[1].split('=',1)[1]
 words=[s.strip() for s in re.split('[,;]',body) if s.strip()]
 return np.array([int(s,2)-(1<<len(s) if s[0]=='1' else 0) for s in words],dtype=np.int64)
X=coe(D/'sel_data.coe').reshape(42,512)
W=[coe(D/'params'/n).reshape(o,i).T for n,o,i in [('fc1.0.weight.coe',128,512),('fc2.0.weight.coe',32,128),('fc3.weight.coe',2,32)]]
B=[coe(D/'params'/n) for n in ['fc1.0.bias.coe','fc2.0.bias.coe','fc3.bias.coe']]
labels=np.array([int(s) for s in re.findall('[01]',(D/'sel_labels.txt').read_text())])
def wrap(a,bits):return ((a+(1<<(bits-1)))&((1<<bits)-1))-(1<<(bits-1))
def evaluate(name,x,w,b,bits,shifts,ops=None):
 a=x
 for layer in range(3):
  a=a@w[layer]+b[layer]
  if layer<2:a=np.maximum(a,0)
  a=wrap(a>>shifts[layer],bits)
 pred=(a[:,0]<a[:,1]).astype(np.int64)
 item={'name':name,'correct':int(sum(pred==labels)),'samples':42,'ties':int(sum(a[:,0]==a[:,1])),'predictions':pred.tolist(),'shifts':shifts,'output_bits':bits,'effective_multiplications_if_rebuilt':ops,'scope':'Offline integer inference only; no retraining, unseen-data evaluation or FPGA implementation; modified models are not equivalent to course INT8.'}
 (R/'results'/f'{name}_samples.csv').write_text('sample,score0,score1,prediction,label,correct\n'+''.join(f'{i},{a[i,0]},{a[i,1]},{pred[i]},{labels[i]},{int(pred[i]==labels[i])}\n' for i in range(42)))
 return item
rows=[evaluate('course_q8',X,W,B,8,[10,9,8],69696),evaluate('course_q4',X,W,B,4,[14,8,9],69696)]
rows.append(evaluate('weight_int4_no_retrain',X,[w>>4 for w in W],[b>>4 for b in B],4,[10,4,5]))
rows.append(evaluate('input_weight_int4_no_retrain',X>>4,[w>>4 for w in W],[B[0]>>8,B[1]>>4,B[2]>>4],4,[6,4,5]))
ranking=np.argsort(np.sum(np.abs(W[0]),axis=0))
for removed in [32,64]:
 w=[a.copy() for a in W];b=[a.copy() for a in B];deleted=ranking[:removed];w[0][:,deleted]=0;b[0][deleted]=0
 rows.append(evaluate(f'fc1_prune_{removed}_no_retrain',X,w,b,8,[10,9,8],(128-removed)*512+(128-removed)*32+64))
(R/'results/model_trials.json').write_text(json.dumps(rows,indent=2))

# Exact INT4 2x2 outer-product packing with signed residual correction.
values=np.arange(-8,8,dtype=np.int64)
w0,w1,x0,x1=np.meshgrid(values,values,values,values,indexing='ij')
a=w0+(w1<<16);b=x0+(x1<<8);remaining=a*b
expected=[w0*x0,w0*x1,w1*x0,w1*x1];errors=0
for e in expected:
 got=wrap(remaining,8);errors+=int(np.count_nonzero(got!=e));remaining=(remaining-got)>>8
proof={'scheme':'(w0+(w1<<16))*(x0+(x1<<8)); peel signed 8-bit fields with residual correction','signed_operands_bits':[21,13],'DSP48E1_capacity_bits':[25,18],'combinations':16**4,'products':4*16**4,'errors':errors,'nonzero_residuals':int(np.count_nonzero(remaining)),'scope':'Exhaustive mathematical proof only; correction hardware, timing, MAC accumulation and integration not implemented. Requires true INT4 inputs and weights, not existing INT8.'}
(R/'results/int4_packing_proof.json').write_text(json.dumps(proof,indent=2))
assert errors==0 and not np.any(remaining)
for row in rows:print(row['name'],row['correct'],row['ties'],row['effective_multiplications_if_rebuilt'])
print('INT4 packing exhaustive proof',proof['products'],'products, errors',errors)
