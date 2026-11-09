"""Run on PYNQ; true caller wall clock includes complete infer()/infer_batch()."""
from pathlib import Path
import argparse,hashlib,json,platform,time
import numpy as np
from lab8_driver import Lab8NPU

def stats(values):
 a=np.asarray(values,dtype=float)
 return {'median':float(np.median(a)),'p95':float(np.percentile(a,95)),
         'min':float(a.min()),'max':float(a.max()),'std':float(a.std())}
def main():
 p=argparse.ArgumentParser();p.add_argument('--bitfile',default=str(Path(__file__).with_name('lab8.bit')))
 p.add_argument('--package',type=Path,help='deployment tar.gz for reproducibility hash')
 p.add_argument('--repeats',type=int,default=100);p.add_argument('--warmup',type=int,default=10)
 p.add_argument('--board-id',required=True);p.add_argument('--arrival-interval-us',type=float,default=0,
  help='optional application sample interval; reports theoretical batch collection delay separately')
 p.add_argument('--output',default='api_board_results.json');args=p.parse_args()
 if args.repeats<100 or args.warmup<1 or args.arrival_interval_us<0:p.error('require repeats >=100, warmup >=1 and nonnegative arrival interval')
 root=Path(__file__).parent;bit=Path(args.bitfile)
 files=[bit,bit.with_suffix('.hwh'),root/'inputs.bin',root/'features.bin',root/'lab8_driver.py']
 if args.package:files.append(args.package)
 if any(not f.exists() for f in files):p.error('missing benchmark identity file')
 hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
 xs=np.fromfile(root/'inputs.bin',np.int8).reshape(42,512)
 gold=np.fromfile(root/'features.bin',np.int8).reshape(42,162);pred=np.fromfile(root/'predictions.bin',np.uint8)
 started=time.perf_counter_ns();n=Lab8NPU(bit);cold=(time.perf_counter_ns()-started)/1000
 report={'scope':'board measurement; only generated on successful real PYNQ run','board_id':args.board_id,
 'platform':platform.platform(),'python':platform.python_version(),'numpy':np.__version__,'hashes':hashes,
 'clock_hz':n.clock_hz,'clock_evidence':n.clock_evidence,'cold_overlay_driver_us':cold,'repeats':args.repeats,'warmup':args.warmup,
 'timing_notes':'ps_end_to_end_us aliases host DMA-call window, excludes packing/clear/parse/MMIO; api_wall_us is full external call. PL boundary differs. Validation and features outside repeated timing.',
 'measurements':[]}
 try:
  for mode in ['scalar','batch']:
   for count in [1,3,8,16,42,48,128]:
    ids=np.arange(count)%42;x=xs[ids].copy()
    t=time.perf_counter_ns()
    if mode=='batch':n.prepare_batch(count)
    allocation=(time.perf_counter_ns()-t)/1000
    rows=[]
    for rep in range(args.warmup+args.repeats):
     t=time.perf_counter_ns()
     values=[n.infer_batch(x)] if mode=='batch' else [n.infer(v) for v in x]
     wall=(time.perf_counter_ns()-t)/1000
     if mode=='batch':
      np.testing.assert_array_equal(values[0]['predictions'],pred[ids]);np.testing.assert_array_equal(values[0]['scores'],gold[ids,160:162])
     else:assert [v['prediction'] for v in values]==pred[ids].tolist()
     row={'api_wall_us':wall, 'api_samples_per_second':count*1e6/wall}
     for key in ['host_dma_window_us','validation_allocation_pack_us','receive_clear_us','parse_statistics_us','api_inside_us','pl_transaction_cycles','compute_cycles']:
      row[key]=sum(v[key] for v in values)
     if rep>=args.warmup:rows.append(row)
    t=time.perf_counter_ns();f=n.features();feature_us=(time.perf_counter_ns()-t)/1000
    np.testing.assert_array_equal(np.concatenate([f['fc1'],f['fc2'],f['fc3']]),gold[ids[-1]])
    report['measurements'].append({'mode':mode,'N':count,'allocation_us':allocation,'feature_read_us':feature_us,
     'collection_delay_first_sample_us':(count-1)*args.arrival_interval_us,
     'collection_delay_mean_sample_us':(count-1)*args.arrival_interval_us/2,
     'collection_delay_scope':'application assumption, not measured',
     'stats':{k:stats([v[k] for v in rows]) for k in rows[0]},'raw':rows})
  import pynq
  report['pynq']=getattr(pynq,'__version__','unknown')
 finally:n.close()
 Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
 print('Saved verified board measurements:',args.output)
if __name__=='__main__':main()
