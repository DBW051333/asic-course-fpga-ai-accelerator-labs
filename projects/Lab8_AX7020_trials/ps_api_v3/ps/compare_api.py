"""Same-overlay, alternating order, full external API A/B timing."""
from pathlib import Path
import argparse,hashlib,importlib,json,platform,time,os
import numpy as np
from pynq import Overlay,allocate
from ax7020_runtime import clock_report,buffer_report
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');p.add_argument('--repeats',type=int,default=100);p.add_argument('--output',default='comparison.json');a=p.parse_args()
xs=np.fromfile(R/'inputs.bin',np.int8).reshape(42,512);gold=np.fromfile(R/'features.bin',np.int8).reshape(42,162);pred=np.fromfile(R/'predictions.bin',np.uint8)
variants={'A':'parent_driver','B':'lab8_driver','P1':'prototype1_driver'}
order=['A','P1','B','B','P1','A'] if a.pilot else ['A','B','B','A','A','B','B','A']
cases=[('scalar',1),('batch',42),('batch',128)] if a.pilot else [('scalar',1)]+[('batch',v) for v in [1,2,3,8,16,42,48,49,64,96,128,256,512]]
overlay=Overlay(str(R/'lab8.bit'));clock=clock_report(overlay.npu_0.mmio)
report={'scope':'Real AX7020, same loaded bit/hwh, identical inputs, external perf_counter_ns includes the complete API; correctness outside timing','client_date':'2026-10-12','board_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'platform':platform.platform(),'python':platform.python_version(),'numpy':np.__version__,'pynq':__import__('pynq').__version__, 'clock':clock,'order':order,'repeats':a.repeats,'warmup':10,'main_metric':'batch N=42 full API median','hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in R.iterdir() if f.suffix in ('.bit','.hwh','.py','.bin')},'blocks':[],'pass':False}
def save():Path(a.output).write_text(json.dumps(report,indent=2)+'\n')
def statistics(rows):
 return {k:{'median':float(np.median([v[k] for v in rows])),'p95':float(np.percentile([v[k] for v in rows],95))} for k in rows[0]}
try:
 for block,var in enumerate(order):
  cls=importlib.import_module(variants[var]).Lab8NPU
  with cls(overlay=overlay,allocator=allocate) as n:
   n.clock_hz=clock['register_derived_hz'];n.clock_evidence=clock
   record={'index':block,'variant':var,'loadavg':list(os.getloadavg()),'measurements':[]}
   for mode,count in cases:
    ids=np.arange(count)%42;x=xs[ids].copy()
    if mode=='batch':n.prepare_batch(count)
    buffers={'tx':buffer_report(n.tx),'rx':buffer_report(n.rx)}
    if mode=='batch':buffers.update(batch_tx=buffer_report(n.batch_tx),batch_rx=buffer_report(n.batch_rx))
    rows=[]
    for rep in range(10+a.repeats):
     t=time.perf_counter_ns()
     v=n.infer(x[0]) if mode=='scalar' else n.infer_batch(x)
     wall=(time.perf_counter_ns()-t)/1000
     if mode=='scalar':assert v['prediction']==int(pred[ids[0]])
     else:
      np.testing.assert_array_equal(v['predictions'],pred[ids]);np.testing.assert_array_equal(v['scores'],gold[ids,160:162])
     if rep>=10:
      row={'api_wall_us':wall,'samples_per_second':count*1e6/wall}
      for key in ['validation_allocation_pack_us','receive_clear_us','host_dma_window_us','parse_statistics_us','api_inside_us','pl_transaction_cycles','compute_cycles']:row[key]=v[key]
      rows.append(row)
    f=n.features();np.testing.assert_array_equal(np.concatenate([f['fc1'],f['fc2'],f['fc3']]),gold[ids[-1]])
    assert n.regs.read(0x14)==0
    record['measurements'].append({'mode':mode,'N':count,'buffers':buffers,'stats':statistics(rows),'raw':rows})
   report['blocks'].append(record);save();print('PASS block',block,var,flush=True)
 report['aggregated']=[]
 for mode,count in cases:
  item={'mode':mode,'N':count,'variants':{}}
  for var in dict.fromkeys(order):
   rows=[row for block in report['blocks'] if block['variant']==var for m in block['measurements'] if m['mode']==mode and m['N']==count for row in m['raw']]
   item['variants'][var]={'stats':statistics(rows),'samples':len(rows)}
  ref=item['variants']['A']['stats'];cand=item['variants']['B']['stats']
  item['api_median_reduction_percent']=100*(1-cand['api_wall_us']['median']/ref['api_wall_us']['median'])
  item['api_p95_reduction_percent']=100*(1-cand['api_wall_us']['p95']/ref['api_wall_us']['p95'])
  report['aggregated'].append(item)
 report['pass']=True;save();print('PASS AX7020 COMPARISON',flush=True)
except Exception as e:report['failure']=repr(e);save();raise
