#!/usr/bin/env python3
"""Integer design-space search. No floating-point arithmetic in inference."""
from pathlib import Path
import csv, itertools, json, re
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LAB6 = ROOT.parent / 'Lab6'
BASE = ROOT.parent / 'Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8'

def read_coe(path):
    body = path.read_text().split('memory_initialization_vector',1)[1].split('=',1)[1]
    words = [v.strip() for v in re.split(r'[,;]',body) if v.strip()]
    return np.array([int(v,2)-(1<<len(v) if v[0]=='1' else 0) for v in words],dtype=np.int64)

X = read_coe(LAB6/'data/sel_data.coe').reshape(42,512)
W = [read_coe(LAB6/'data/params'/f).reshape(no,ni).T for f,no,ni in
     [('fc1.0.weight.coe',128,512),('fc2.0.weight.coe',32,128),('fc3.weight.coe',2,32)]]
B = [read_coe(LAB6/'data/params'/f) for f in ['fc1.0.bias.coe','fc2.0.bias.coe','fc3.bias.coe']]
LABELS = np.array([int(v) for v in re.findall('[01]',(LAB6/'data/sel_labels.txt').read_text())])
assert len(LABELS)==42

def quant(a,width,shift,mode):
    if mode=='round_sat':
        a=a+((1<<(shift-1)) if shift else 0) # nearest, ties toward +infinity
    q=a>>shift
    lo,hi=-(1<<(width-1)),(1<<(width-1))-1
    overflow=int(np.count_nonzero((q<lo)|(q>hi)))
    if mode=='floor_wrap':
        q=((q-lo)&((1<<width)-1))+lo
    else:
        q=np.clip(q,lo,hi)
    return q,overflow

def minshift(a,width,mode):
    for s in range(64):
        q=a+((1<<(s-1)) if mode=='round_sat' and s else 0)
        if np.all((q>>s)>=-(1<<(width-1))) and np.all((q>>s)<(1<<(width-1))):return s
    raise ValueError('range')

def infer(x,widths,shifts,mode,product_cut=0):
    a=x; layers=[];ranges=[];counts=[]
    for k in range(3):
        if k==0 and product_cut:
            products=a[:,None,:]*W[0].T[None,:,:]
            products=((products+(1<<(product_cut-1)))>>product_cut)<<product_cut
            raw=products.sum(axis=-1)+B[0]
        else:
            raw=a@W[k]+B[k] # preserve Lab6's original 8-bit bias convention
        if k<2:raw=np.maximum(raw,0)
        a,n=quant(raw,widths[k],shifts[k],mode)
        layers.append(a);ranges.append([int(raw.min()),int(raw.max())]);counts.append(n)
    return layers,ranges,counts

def metrics(layers,ranges,counts,widths,shifts,mode,baseline_pred):
    c=layers[-1];pred=(c[:,0]<c[:,1]).astype(int)
    return dict(widths=list(widths),shifts=list(shifts),mode=mode,
        correct=int(np.count_nonzero(pred==LABELS)),accuracy=float(np.mean(pred==LABELS)),
        ties=int(np.count_nonzero(c[:,0]==c[:,1])),
        disagreements=int(np.count_nonzero(pred!=baseline_pred)),
        overflow_counts=counts,raw_ranges=ranges,
        wrong_samples=np.where(pred!=LABELS)[0].tolist())

def main():
    (ROOT/'results').mkdir(exist_ok=True)
    a=np.maximum(X@W[0]+B[0],0);b=np.maximum(a@W[1]+B[1],0);c=b@W[2]+B[2]
    bp=(c[:,0]<c[:,1]).astype(int)
    assert c[0].tolist()==[1444462170,-1667237270]
    assert [int(np.abs(z).max()) for z in [a,b,c]]==[80805,39386422,17379948761]
    baseline=dict(name=BASE.name,correct=int(np.count_nonzero(bp==LABELS)),ties=int(np.count_nonzero(c[:,0]==c[:,1])),
                  max_abs=[int(np.abs(z).max()) for z in [a,b,c]],wrong_samples=np.where(bp!=LABELS)[0].tolist())
    rows=[]
    widths_list=[(4,4,4),(6,6,6),(8,8,8),(10,10,10),(12,12,12),(16,16,16),
                 (4,8,8),(6,8,8),(8,4,8),(8,6,8),(8,8,16),(6,6,16)]
    for widths,mode in itertools.product(widths_list,['floor_wrap','floor_sat','round_sat']):
        s1base=minshift(a,widths[0],mode)
        for s1 in range(max(0,s1base-2),s1base+3):
            q1,n1=quant(a,widths[0],s1,mode)
            raw2=np.maximum(q1@W[1]+B[1],0)
            s2base=minshift(raw2,widths[1],mode)
            for s2 in range(max(0,s2base-2),s2base+3):
                q2,n2=quant(raw2,widths[1],s2,mode)
                raw3=q2@W[2]+B[2]
                s3base=minshift(raw3,widths[2],mode)
                for s3 in range(max(0,s3base-2),s3base+3):
                    q3,n3=quant(raw3,widths[2],s3,mode)
                    rows.append(metrics([q1,q2,q3],[[int(a.min()),int(a.max())],[int(raw2.min()),int(raw2.max())],
                          [int(raw3.min()),int(raw3.max())]],[n1,n2,n3],widths,[s1,s2,s3],mode,bp))
    (ROOT/'results/quantization_search.json').write_text(json.dumps(rows,indent=2))
    with (ROOT/'results/quantization_search.csv').open('w',newline='') as f:
        fields=['widths','shifts','mode','correct','accuracy','ties','disagreements','overflow_counts','wrong_samples']
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    # Mandatory Lab6 versions, controls for DSP redistribution, and additional precision variants.
    candidates=[]
    def add(name,widths,shifts,mode,dsp1=168,tail='standard',product_cut=0,product_cut_stage=None):
        layers,ranges,counts=infer(X,widths,shifts,mode,product_cut)
        m=metrics(layers,ranges,counts,widths,shifts,mode,bp)
        m.update(name=name,dsp1=dsp1,tail=tail)
        if product_cut:m['product_cut']=product_cut
        if product_cut_stage:m['product_cut_stage']=product_cut_stage
        candidates.append(m)
    add('q8_lab6_d168',(8,8,8),(10,9,8),'floor_wrap')
    add('q4_lab6_d168',(4,4,4),(14,8,9),'floor_wrap')
    add('q8_lab6_d180',(8,8,8),(10,9,8),'floor_wrap',180)
    add('q8_lab6_pack_d200',(8,8,8),(10,9,8),'floor_wrap',200,'packed')
    add('q4_lab6_lut_d220',(4,4,4),(14,8,9),'floor_wrap',220,'lut')
    for widths in [(6,6,6),(8,8,8),(8,6,8),(4,8,8)]:
        choices=[r for r in rows if tuple(r['widths'])==widths and r['mode']=='round_sat']
        best=min(choices,key=lambda r:(-r['correct'],r['ties'],sum(r['overflow_counts']),r['disagreements'],sum(r['shifts'])))
        add('q'+'_'.join(map(str,widths))+'_round_pack_d200',widths,best['shifts'],'round_sat',200,'packed')
    for cut in [1,2,3,4,6,8]:
        add(f'q8_product{cut}_pack_d200',(8,8,8),(10,9,8),'floor_wrap',200,'packed',cut)
    for cut in [4,6]:
        add(f'q8_product{cut}_prereg_pack_d200',(8,8,8),(10,9,8),'floor_wrap',200,'packed',cut,'register')
    add('q8_lab6_rompack_d200',(8,8,8),(10,9,8),'floor_wrap',200,'packed_rom')
    add('q8_product6_prereg_rompack_d200',(8,8,8),(10,9,8),'floor_wrap',200,'packed_rom',6,'register')
    add('q8_lab6_tree8_rompack_d200',(8,8,8),(10,9,8),'floor_wrap',200,'packed_rom')
    candidates[-1]['tree_stages']=8
    (ROOT/'results/baseline.json').write_text(json.dumps(baseline,indent=2))
    (ROOT/'results/candidates.json').write_text(json.dumps(candidates,indent=2))
    print('baseline',baseline,'searched',len(rows))
    for r in candidates:print(r['name'],r['shifts'],r['correct'],r['ties'],r['overflow_counts'])

if __name__=='__main__':main()
