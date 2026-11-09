"""AX7020 sequential board acceptance, with raw identity and recovery evidence."""
from pathlib import Path
import hashlib,json,platform,time
import numpy as np
from lab8_driver import Lab8NPU
from ax7020_runtime import buffer_report
R=Path(__file__).resolve().parent
out=R/'board_acceptance';out.mkdir(exist_ok=True)
xs=np.fromfile(R/'inputs.bin',np.int8).reshape(42,512)
pred=np.fromfile(R/'predictions.bin',np.uint8)
gold=np.fromfile(R/'features.bin',np.int8).reshape(42,162)
report={'board':'AX7020','started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'platform':platform.platform(),
        'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in R.iterdir() if p.suffix in ('.bit','.hwh','.py','.bin')},
        'phases':[], 'pass':False, 'power_measured':False}
def save(): (out/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n')
def phase(name,**values):
    report['phases'].append({'name':name,'pass':True,**values});save();print('PASS',name,flush=True)
save()
try:
    with Lab8NPU(R/'lab8.bit') as n:
        report['clock']=n.clock_evidence
        phase('overlay_registers',signature=hex(n.regs.read(0)),buffers=n.buffer_evidence,
              dma_registers=str(n.dma.register_map))
        first=n.infer(xs[0]);assert first['prediction']==pred[0]
        f=n.features();np.testing.assert_array_equal(np.concatenate(list(f[k] for k in ['fc1','fc2','fc3'])),gold[0])
        phase('first_sample',result=first)
    with Lab8NPU(R/'lab8.bit') as n:
        scalar=[]
        for i,x in enumerate(xs):
            v=n.infer(x);assert v['prediction']==pred[i];scalar.append(v)
            f=n.features();np.testing.assert_array_equal(np.concatenate([f['fc1'],f['fc2'],f['fc3']]),gold[i])
        assert n.regs.read(0x10)==42 and n.regs.read(0x14)==0
        phase('scalar42_all_layers',samples=42,feature_values=6804,errors=0,completed=42,raw=scalar)
        for count in [1,3,8,16,42,48,128]:
            ids=np.arange(count)%42
            repeats=[]
            for repeat in range(3):
                v=n.infer_batch(xs[ids]);np.testing.assert_array_equal(v['predictions'],pred[ids]);np.testing.assert_array_equal(v['scores'],gold[ids,160:162])
                f=n.features();np.testing.assert_array_equal(np.concatenate([f['fc1'],f['fc2'],f['fc3']]),gold[ids[-1]])
                repeats.append({k:value for k,value in v.items() if k not in ('predictions','scores')})
            phase('batch_'+str(count),repeated_batches=3,classes_scores_and_last_features=True,
                  buffers=n.buffer_evidence.copy(),raw=repeats)
        # Truncated CMD1 (header only) is a framing error; then recover.
        n.tx[:8]=np.frombuffer((1).to_bytes(8,'little'),np.uint8)
        received,elapsed=n._exchange(8,8)
        report['malformed_response']={'received':received,'code':int(n.rx[0])};save()
        assert received==1 and int(n.rx[0])==0xE3
        assert n.regs.read(0x14)==1
        error_state={hex(o):n.regs.read(o) for o in (8,0x10,0x14,0x28,0x2C)}
        v=n.infer(xs[0]);assert v['prediction']==pred[0]
        n.reset_dma();v=n.infer(xs[1]);assert v['prediction']==pred[1]
        phase('malformed_packet_and_reset_recovery',received=received,error_state=error_state,
              recovery_prediction=v['prediction'])
    with Lab8NPU(R/'lab8.bit') as n:
        v=n.infer_batch(xs);np.testing.assert_array_equal(v['predictions'],pred);np.testing.assert_array_equal(v['scores'],gold[:,160:162])
        phase('overlay_reload_recovery',samples=42,errors=n.regs.read(0x14))
    import pynq
    report['pynq']=pynq.__version__;report['python']=platform.python_version()
    report['pass']=True;save();print('PASS AX7020 LAB8 ACCEPTANCE',flush=True)
except Exception as exc:
    report['failure']=repr(exc);save();raise
