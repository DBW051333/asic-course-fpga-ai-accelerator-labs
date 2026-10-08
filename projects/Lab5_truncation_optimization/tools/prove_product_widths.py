#!/usr/bin/env python3
"""Check every FC1 tree node for all INT8 input intervals and fixed weights."""
import json
import numpy as np
from search_quantization import ROOT,W,B

def main():
    weights=W[0].T
    raw0=weights*(-128);raw1=weights*127
    low=np.minimum(raw0,raw1);high=np.maximum(raw0,raw1)
    records=[]
    for k in range(1,9):
        half=1<<(k-1)
        lo=(low+half)>>k;hi=(high+half)>>k
        proof=[]
        for level in range(9):
            n=1<<level;width=16-k+level
            a=lo.reshape(128,-1,n).sum(axis=2);b=hi.reshape(128,-1,n).sum(axis=2)
            assert a.min()>=-(1<<(width-1)) and b.max()<(1<<(width-1))
            proof.append(dict(products_per_node=n,width=width,min=int(a.min()),max=int(b.max())))
        accum_lo=(lo.reshape(128,2,256).sum(axis=2)<<k)
        accum_hi=(hi.reshape(128,2,256).sum(axis=2)<<k)
        prefix_lo=np.cumsum(accum_lo,axis=1)+B[0][:,None]
        prefix_hi=np.cumsum(accum_hi,axis=1)+B[0][:,None]
        assert prefix_lo.min()>=-(1<<22) and prefix_hi.max()<(1<<22)
        # Product rounding before the register cannot overflow a 16-bit product.
        assert low.min()+half>=-32768 and high.max()+half<=32767
        records.append(dict(product_cut=k,status='pass',tree_nodes=proof,
             accumulator_width=23,prefix_min=int(prefix_lo.min()),prefix_max=int(prefix_hi.max()),
             fc1_absolute_error_bound=512*half))
    (ROOT/'results/product_width_proof.json').write_text(json.dumps(records,indent=2))
    print('PASS: K=1..8 tree nodes and FC1 accumulation widths for ALL signed INT8 inputs and fixed weights')

if __name__=='__main__':main()
