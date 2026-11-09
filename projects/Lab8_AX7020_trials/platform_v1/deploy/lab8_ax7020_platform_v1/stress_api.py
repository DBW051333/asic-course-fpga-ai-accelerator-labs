"""Software-path acceptance and finite continuous AX7020 reliability test."""
from pathlib import Path
import json,time,hashlib
import numpy as np
from lab8_driver import Lab8NPU
R=Path(__file__).resolve().parent
xs=np.fromfile(R/'inputs.bin',np.int8).reshape(42,512);gold=np.fromfile(R/'features.bin',np.int8).reshape(42,162);pred=np.fromfile(R/'predictions.bin',np.uint8)
report={'client_date':'2026-10-12','scope':'Real AX7020 functional/reliability checks; not timed A/B benchmark','pass':False,'phases':[],'driver_sha256':hashlib.sha256((R/'lab8_driver.py').read_bytes()).hexdigest()}
def save(): (R/'stress_results.json').write_text(json.dumps(report,indent=2)+'\n')
def check(n,x,ids):
 v=n.infer_batch(x);np.testing.assert_array_equal(v['predictions'],pred[ids]);np.testing.assert_array_equal(v['scores'],gold[ids,160:162]);return v
def feature(n,g):
 f=n.features();np.testing.assert_array_equal(np.concatenate([f['fc1'],f['fc2'],f['fc3']]),g);return f
def phase(name,**kw):report['phases'].append({'name':name,'pass':True,**kw});save();print('PASS',name,flush=True)
save()
try:
 with Lab8NPU(R/'lab8.bit') as n:
  report['clock']=n.clock_evidence
  for dtype in [np.int8,np.int16,np.int32,np.int64]:
   check(n,xs[:3].astype(dtype),np.arange(3));feature(n,gold[2])
  check(n,np.asfortranarray(xs[:3]),np.arange(3));feature(n,gold[2])
  storage=np.empty((3,1024),np.int8);storage[:,::2]=xs[:3];check(n,storage[:,::2],np.arange(3));feature(n,gold[2])
  mutable=xs[:3].copy();old=check(n,mutable,np.arange(3));snapshot={k:old[k].copy() for k in ['predictions','scores']}
  f=feature(n,gold[2]);fsnapshot={k:f[k].copy() for k in ['fc1','fc2','fc3']}
  mutable[:]=xs[21:24];check(n,mutable,np.arange(21,24));feature(n,gold[23]);n.prepare_batch(512)
  for key,v in snapshot.items():np.testing.assert_array_equal(old[key],v)
  for key,v in fsnapshot.items():np.testing.assert_array_equal(f[key],v)
  phase('dtypes_strides_mutable_input_result_lifetime')
  for entry in json.loads((R/'extra_reference.json').read_text()):
   for dtype in ([np.uint8,np.uint16,np.uint32,np.uint64,np.int16] if min(entry['input'])>=0 else [np.int8,np.int16]):
    x=np.asarray(entry['input'],dtype=dtype)
    v=n.infer(x);assert v['prediction']==entry['prediction'];feature(n,np.array(entry['features'],np.int8))
    v=n.infer_batch(x.reshape(1,512));assert v['predictions'][0]==entry['prediction'];np.testing.assert_array_equal(v['scores'][0],entry['features'][-2:]);feature(n,np.array(entry['features'],np.int8))
  phase('extra_integer_reference',samples=4,note='additional boundary/random checks, not additional course accuracy samples')
  before=n.regs.read(0x10)
  rejected=0
  for x in [np.zeros((0,512),np.int8),np.zeros((1,511),np.int8),np.zeros((1,512),np.float32),np.zeros((1,512),np.bool_),np.full((1,512),128,np.uint64),np.full((1,512),2**64-1,np.uint64),np.full((1,512),-129,np.int16)]:
   try:n.infer_batch(x)
   except ValueError:rejected+=1
   else:raise AssertionError('invalid input accepted')
  assert n.regs.read(0x10)==before
  phase('invalid_input_rejection',cases=rejected,hardware_jobs_unchanged=True)
  counts=[1,2,3,8,16,42,48,128,256,512];inputs={count:xs[np.arange(count)%42].copy() for count in counts}
  preserved=check(n,inputs[42],np.arange(42));saved=preserved['scores'].copy()
  started=time.monotonic();iterations=0;samples=0;features=0;min_tx=None;max_end=0
  while time.monotonic()-started<120:
   count=counts[iterations%len(counts)];ids=np.arange(count)%42
   check(n,inputs[count],ids);samples+=count;iterations+=1
   if iterations%50==0:feature(n,gold[ids[-1]]);features+=162
   if iterations%500==0:
    report['progress']={'iterations':iterations,'samples':samples,'elapsed_seconds':time.monotonic()-started};save()
  np.testing.assert_array_equal(preserved['scores'],saved)
  assert n.regs.read(0x14)==0
  phase('continuous_120_seconds',elapsed_seconds=time.monotonic()-started,transactions=iterations,samples=samples,feature_values=features,errors=0,batch_sizes=counts,buffers=n.buffer_evidence,note='N>42 repeats course inputs; not new accuracy samples')
  n.reset_dma();check(n,inputs[42],np.arange(42));feature(n,gold[41]);phase('post_stress_reset_recovery')
 report['pass']=True;save();print('PASS AX7020 SOFTWARE STRESS',flush=True)
except Exception as e:report['failure']=repr(e);save();raise
