"""Decode-only attribution, no MMIO/DMA. Not a full API acceptance metric."""
from pathlib import Path
import json,time,importlib,textwrap
import numpy as np
R=Path(__file__).resolve().parent
variants={'A':'parent_driver','P1':'prototype1_driver','B':'prototype2_driver'}
functions={}
for key,name in variants.items():
 module=importlib.import_module(name);source=(R/(name+'.py')).read_text()
 begin=source.index('        data = self._batch_rx_bytes[:count * 8].copy()') if key=='A' else source.index('        if received != count * 8:')
 end=source.index('        if self.regs.read(0x20)',begin)
 block=textwrap.dedent(source[begin:end])
 tail='return data[:,0].copy(), scores' if key=='A' else 'return predictions, scores'
 scope=dict(module.__dict__);exec('def decode(self,count,received):\n'+textwrap.indent(block+tail+'\n','    '),scope);functions[key]=scope['decode']
report={'scope':__doc__,'order':['A','P1','B','B','P1','A'],'warmup':20,'repeats_per_block':200,'results':[]}
for count in [1,2,3,8,16,32,42,48,64,80,96,128,256,512]:
 data=np.zeros((count,8),np.uint8);data[:,1]=8;data[:,2]=245
 n=type('Input',(),{'_batch_rx_bytes':data.reshape(-1)})()
 rows={k:[] for k in variants}
 for key in report['order']:
  for i in range(220):
   start=time.perf_counter_ns();pred,scores=functions[key](n,count,count*8);elapsed=(time.perf_counter_ns()-start)/1000
   assert np.all(pred==0) and np.all(scores[:,0]==8) and np.all(scores[:,1]==-11)
   if i>=20:rows[key].append(elapsed)
 report['results'].append({'N':count,'variants':{k:{'median_us':float(np.median(v)),'p95_us':float(np.percentile(v,95)),'raw_us':v} for k,v in rows.items()}})
(R/'parse_microbench.json').write_text(json.dumps(report,indent=2)+'\n')
for item in report['results']:print(item['N'],{k:round(v['median_us'],3) for k,v in item['variants'].items()},flush=True)
