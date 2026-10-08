#!/usr/bin/env python3
"""Exhaustive signed packing arithmetic for all supported activation widths."""
from pathlib import Path
import numpy as np
from search_quantization import ROOT

def main():
    w0=np.repeat(np.arange(-128,128,dtype=np.int64),256)
    w1=np.tile(np.arange(-128,128,dtype=np.int64),256)
    records=[]
    for iw in [4,6,8]:
        count=0;pw=iw+8;ppw=iw+25
        for x in range(-(1<<(iw-1)),1<<(iw-1)):
            packed=(w1<<16)+w0
            bits=(packed*x)&((1<<ppw)-1)
            low=((bits&((1<<pw)-1))^(1<<(pw-1)))-(1<<(pw-1))
            highbits=bits>>16
            high=((highbits^(1<<(ppw-17)))-(1<<(ppw-17)))+((bits>>15)&1)
            assert np.array_equal(low,x*w0)
            assert np.array_equal(high,x*w1)
            count+=len(w0)
        records.append(f'IW={iw}: PASS {count} combinations of x,w0,w1, exact low and corrected high products')
    (ROOT/'results/packing_proof.txt').write_text('\n'.join(records)+'\n')
    print('\n'.join(records))

if __name__=='__main__':main()
