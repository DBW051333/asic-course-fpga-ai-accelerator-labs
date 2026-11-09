"""Host tests for PS packet construction, results and failure handling.
The fake transport checks packets against the independent verified dataset;
this is not a board benchmark or a simulation of the AXI DMA IP.
"""
from pathlib import Path
import sys,unittest,tempfile,json,contextlib,io
from unittest.mock import patch
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'ps'))
import importlib
variant=sys.argv[1] if len(sys.argv)>1 else 'lab8_driver'
Lab8NPU=importlib.import_module(variant).Lab8NPU
import run_lab8
xs=np.fromfile(R/'ps/inputs.bin',np.int8).reshape(42,512)
gold=np.fromfile(R/'ps/features.bin',np.uint8).reshape(42,162)
preds=np.fromfile(R/'ps/predictions.bin',np.uint8)
class Buffer(np.ndarray):
    def freebuffer(self):self.freed=True
    def invalidate(self):self.invalidated=True
class Registers:
    def __init__(self):self.values={0:0x4c414238,12:166666672,16:0,20:0}
    def read(self,addr):return self.values.get(addr,0)
    def write(self,addr,value):
        if addr==4 and value&1:self.values.update({16:0,20:0,8:0})
class Channel:
    def __init__(self,parent,recv):self.parent=parent;self.recv=recv;self.idle=True;self.running=True;self.error=False;self.transferred=0
    def transfer(self,buf,nbytes):
        self.idle=False
        self._active_buffer=buf
        if self.recv:self.parent.destination=buf;self.parent.capacity=nbytes
        else:self.parent.exchange(buf,nbytes)
    def wait(self):
        self.parent.waits+=1
        if self.recv:self.transferred=self.parent.length
    def start(self):self.running=True;self.idle=True
class DMA:
    def __init__(self,regs):
        self.regs=regs;self.mmio=self;self.sendchannel=Channel(self,False);self.recvchannel=Channel(self,True)
        self.register_map='fake DMA registers';self.last=None;self.length=0;self.waits=0;self.corrupt_length=False
    def read(self,addr):
        if addr in [4,0x34]:
            c=self.sendchannel if addr==4 else self.recvchannel
            return (2 if c.idle else 0) | (0 if c.running else 1) | (0x40 if c.error else 0)
        if addr==0x28:return self.regs.read(32)
        if addr==0x58:return self.length
        return 0
    def write(self,addr,value):
        if value==4:self.sendchannel.idle=True;self.recvchannel.idle=True
    def exchange(self,buf,nbytes):
        cmd=int.from_bytes(bytes(buf[:8]),'little')
        if cmd==1:
            assert nbytes==520 and self.capacity==8
            candidates=[i for i,x in enumerate(xs) if bytes(buf[8:520])==x.tobytes()]
            assert candidates,'wrong signed input order or sample data'
            self.last=candidates[0];answer=bytes([preds[self.last]])
            self.regs.values.update({16:self.regs.read(16)+1,24:216,28:250,32:520,36:1})
        elif cmd & 0xffffffff == 3:
            count = cmd >> 32
            assert nbytes == 8 + 512 * count and self.capacity == 8 * count
            answer = bytearray()
            for sample in range(count):
                payload = bytes(buf[8+512*sample:8+512*(sample+1)])
                candidates = [i for i,x in enumerate(xs) if x.tobytes() == payload]
                assert candidates, 'invalid batch byte order'
                self.last = candidates[0]
                answer += bytes([preds[self.last],gold[self.last,160],gold[self.last,161],0,0,0,0,0])
            self.regs.values.update({16:self.regs.read(16)+count,24:216,28:8000,32:nbytes,36:8*count})
        elif cmd==2:
            assert nbytes==8 and self.capacity==168 and self.last is not None
            answer=gold[self.last].tobytes();self.regs.values.update({32:8,36:162})
        else:raise AssertionError('bad command encoding')
        self.destination[:len(answer)]=np.frombuffer(answer,np.uint8);self.length=len(answer)
        if self.corrupt_length:self.length-=1
        self.sendchannel.idle=True;self.recvchannel.idle=True
class Overlay:
    def __init__(self):
        self.regs=Registers();self.npu_0=type('IP',(),{'mmio':self.regs})();self.axi_dma_0=DMA(self.regs)
def allocate(shape,dtype):return np.zeros(shape,dtype).view(Buffer)
def device():return Lab8NPU(overlay=Overlay(),allocator=allocate)
class Tests(unittest.TestCase):
    def test_dma_status_error_priority_halt_timeout_and_actual_length(self):
        with device() as n:
            n.infer(xs[0])
            self.assertEqual(n.dma.sendchannel.transferred,520)
            self.assertEqual(n.dma.recvchannel.transferred,1)
            for channel in [n.dma.sendchannel,n.dma.recvchannel]:
                channel.error=True;channel.idle=True
                with self.assertRaisesRegex(RuntimeError,'DMA error'):n._wait_dma()
                channel.error=False
                channel.running=False
                with self.assertRaisesRegex(RuntimeError,'halted'):n._wait_dma()
                channel.running=True
            n.timeout=.001;n.dma.recvchannel.idle=False
            with self.assertRaises(TimeoutError):n._wait_dma()
            n.reset_dma();self.assertEqual(n.infer(xs[1])['prediction'],int(preds[1]))

    def test_batch_rejects_corrupt_class_scores_padding_and_counters(self):
        with device() as n:
            original=n.dma.exchange
            for column,value in [(0,2),(1,128),(3,1),(7,1)]:
                def corrupt(buf,nbytes):
                    original(buf,nbytes)
                    if column==1:
                        n.dma.destination[0]=0;n.dma.destination[1]=128;n.dma.destination[2]=127
                    else:n.dma.destination[column]=value
                with patch.object(n.dma,'exchange',side_effect=corrupt):
                    with self.assertRaises(RuntimeError):n.infer_batch(xs[:3])
            def counters(buf,nbytes):original(buf,nbytes);n.regs.values[32]=1
            with patch.object(n.dma,'exchange',side_effect=counters):
                with self.assertRaisesRegex(RuntimeError,'byte counters'):n.infer_batch(xs[:3])
            np.testing.assert_array_equal(n.infer_batch(xs[:3])['predictions'],preds[:3])

    def test_signed_score_extremes_ties_and_writable_snapshots(self):
        values=[-128,-127,-1,0,1,126,127]
        pairs=[(a,b) for a in values for b in values]
        with device() as n:
            original=n.dma.exchange
            for count in [1,7,48,49,64,128]:
                scores=np.array([pairs[i%49] for i in range(count)],np.int8)
                inputs=np.repeat(xs[:1],count,axis=0)
                packet=np.zeros((count,8),np.uint8);packet[:,0]=scores[:,0]<scores[:,1];packet[:,1:3]=scores.view(np.uint8)
                def response(buf,nbytes):original(buf,nbytes);n.dma.destination[:packet.size]=packet.reshape(-1)
                with patch.object(n.dma,'exchange',side_effect=response):result=n.infer_batch(inputs)
                np.testing.assert_array_equal(result['scores'],scores);np.testing.assert_array_equal(result['predictions'],packet[:,0])
                self.assertEqual(result['scores'].dtype,np.int8)
                self.assertTrue(result['scores'].flags.writeable and result['predictions'].flags.writeable)
                n.infer_batch(xs[:3]);n.prepare_batch(256)
                np.testing.assert_array_equal(result['scores'],scores)
                self.assertFalse(np.shares_memory(result['scores'],n.batch_rx))
                packet[0,0]=1  # -128 == -128 tie must classify as 0.
                with patch.object(n.dma,'exchange',side_effect=response):
                    with self.assertRaisesRegex(RuntimeError,'signed scores'):n.infer_batch(inputs)

    def test_every_padding_byte_and_invalid_class_bits(self):
        with device() as n:
            original=n.dma.exchange
            for count in [3,49]:
                inputs=np.resize(xs,(count,512))
                for row in [0,1,count-1]:
                    for column in [0,3,4,5,6,7]:
                        for value in ([2,4,8,16,32,64,128,255] if column==0 else [1,128,255]):
                            def response(buf,nbytes):original(buf,nbytes);n.dma.destination[row*8+column]=value
                            with patch.object(n.dma,'exchange',side_effect=response):
                                with self.assertRaisesRegex(RuntimeError,'Invalid batch response'):n.infer_batch(inputs)
            np.testing.assert_array_equal(n.infer_batch(xs[:3])['predictions'],preds[:3])

    def test_live_statistics_and_receive_lengths_each_call(self):
        with device() as n:
            original=n.dma.exchange
            for tx_delta,rx_delta in [(1,0),(0,1)]:
                def counters(buf,nbytes):
                    original(buf,nbytes);n.regs.values[32]+=tx_delta;n.regs.values[36]+=rx_delta
                with patch.object(n.dma,'exchange',side_effect=counters):
                    with self.assertRaisesRegex(RuntimeError,'byte counters'):n.infer_batch(xs[:3])
            for actual in [0,23,25]:
                def length(buf,nbytes):original(buf,nbytes);n.dma.length=actual
                with patch.object(n.dma,'exchange',side_effect=length):
                    with self.assertRaisesRegex(RuntimeError,'bytes='):n.infer_batch(xs[:3])
            for cycles,transaction in [(217,999),(222,1001)]:
                def stats(buf,nbytes):
                    original(buf,nbytes);n.regs.values[24]=cycles;n.regs.values[28]=transaction
                with patch.object(n.dma,'exchange',side_effect=stats):r=n.infer_batch(xs[:3])
                self.assertEqual(r['compute_cycles'],cycles)
                self.assertEqual(r['pl_transaction_cycles'],transaction)

    def test_all_course_samples(self):
        with device() as n:
            for i,x in enumerate(xs):
                r=n.infer(x);self.assertEqual(r['prediction'],int(preds[i]));self.assertEqual(r['compute_us'],216*1e6/166666672)
                f=n.features();np.testing.assert_array_equal(np.concatenate([f['fc1'],f['fc2'],f['fc3']]).view(np.uint8),gold[i])
            self.assertEqual(n.regs.read(16),42);self.assertEqual(n.dma.waits,0);self.assertTrue(n.rx.invalidated)
        self.assertTrue(n.tx.freed and n.rx.freed)
    def test_batch_and_buffer_reuse(self):
        with device() as n:
            n.prepare_batch(42)
            tx,rx=n.batch_tx,n.batch_rx
            r=n.infer_batch(xs)
            np.testing.assert_array_equal(r['predictions'],preds)
            np.testing.assert_array_equal(r['scores'].view(np.uint8),gold[:,160:162])
            self.assertEqual(n.dma.waits,0);self.assertTrue(n.batch_rx.invalidated)
            self.assertIs(n.batch_tx,tx)
            self.assertIs(n.batch_rx,rx)
            f=n.features()
            np.testing.assert_array_equal(np.concatenate([f['fc1'],f['fc2'],f['fc3']]).view(np.uint8),gold[-1])
            np.testing.assert_array_equal(n.infer_batch(xs[:1])['predictions'],preds[:1])
        self.assertTrue(tx.freed and rx.freed)

    def test_invalid_batches_and_failure_recovery(self):
        with device() as n:
            for x in [np.zeros((0,512),np.int8),np.zeros((1,511),np.int8),np.zeros((1,512),float),np.full((1,512),128)]:
                with self.assertRaises(ValueError):n.infer_batch(x)
            for count in [0,16384,1.5]:
                with self.assertRaises(ValueError):n.prepare_batch(count)
            n.dma.corrupt_length=True
            with self.assertRaisesRegex(RuntimeError,'batch response'):n.infer_batch(xs[:3])
            n.dma.corrupt_length=False
            with patch.object(n,'_wait_dma',side_effect=TimeoutError('injected batch timeout')):
                with self.assertRaises(TimeoutError):n.infer_batch(xs[:3])
            np.testing.assert_array_equal(n.infer_batch(xs[:3])['predictions'],preds[:3])

    def test_fresh_dma_batch_before_scalar(self):
        with device() as n:
            for c in (n.dma.sendchannel,n.dma.recvchannel):
                c.idle=False;c._first_transfer=True
            n.prepare_batch(3)
            np.testing.assert_array_equal(n.infer_batch(xs[:3])['predictions'],preds[:3])
            for c in (n.dma.sendchannel,n.dma.recvchannel):
                c.idle=False;c._first_transfer=False
            with self.assertRaisesRegex(RuntimeError,'Cannot resize'):
                n.prepare_batch(8)
            for c in (n.dma.sendchannel,n.dma.recvchannel):c.idle=True

    def test_integer_types_strides_and_input_updates(self):
        with device() as n:
            for dtype in [np.int8,np.int16,np.int32,np.int64]:
                v=xs[:3].astype(dtype)
                np.testing.assert_array_equal(n.infer_batch(v)['predictions'],preds[:3])
                self.assertEqual(n.infer(v[0])['prediction'],int(preds[0]))
            storage=np.empty((3,1024),np.int8);storage[:,::2]=xs[:3]
            np.testing.assert_array_equal(n.infer_batch(storage[:,::2])['scores'].view(np.uint8),gold[:3,160:162])
            np.testing.assert_array_equal(n.infer_batch(np.asfortranarray(xs[:3]))['predictions'],preds[:3])
            mutable=xs[:3].copy();n.infer_batch(mutable);mutable[:]=xs[21:24]
            np.testing.assert_array_equal(n.infer_batch(mutable)['predictions'],preds[21:24])
            with self.assertRaises(ValueError):n.infer_batch(np.full((3,512),128,np.uint64))
            with self.assertRaises(ValueError):n.infer_batch(np.full((3,512),2**64-1,np.uint64))
            with self.assertRaises(ValueError):n.infer_batch(np.full((3,512),-129,np.int16))
            with self.assertRaises(ValueError):n.infer_batch(np.zeros((3,512),np.bool_))
            with self.assertRaises(ValueError):n.infer_batch(np.zeros((3,512),np.float32))

    def test_result_lifetime_and_expansion_failure(self):
        with device() as n:
            result=n.infer_batch(xs[:3]);saved={k:result[k].copy() for k in ['predictions','scores']}
            features=n.features();saved_features={k:features[k].copy() for k in ['fc1','fc2','fc3']}
            n.infer_batch(xs[21:24]);n.features();n.infer_batch(xs)
            for k,v in saved.items():np.testing.assert_array_equal(result[k],v)
            for k,v in saved_features.items():np.testing.assert_array_equal(features[k],v)
            self.assertFalse(np.shares_memory(result['predictions'],n.batch_rx))
            self.assertFalse(np.shares_memory(result['scores'],n.batch_rx))
            old_tx,old_rx=n.batch_tx,n.batch_rx;created=[]
            def fail_second(shape,dtype):
                if created:raise MemoryError('injected allocation failure')
                v=allocate(shape,dtype);created.append(v);return v
            n._allocator=fail_second
            with self.assertRaises(MemoryError):n.prepare_batch(128)
            self.assertTrue(created[0].freed)
            self.assertIs(n.batch_tx,old_tx);self.assertIs(n.batch_rx,old_rx)
            np.testing.assert_array_equal(n.infer_batch(xs[:3])['predictions'],preds[:3])

    def test_invalid_inputs(self):
        with device() as n:
            for x in [np.zeros(511,np.int8),np.zeros(512,float),np.full(512,128),np.full(512,-129)]:
                with self.assertRaises(ValueError):n.infer(x)
    def test_bad_received_length(self):
        with device() as n:
            n.dma.corrupt_length=True
            with self.assertRaisesRegex(RuntimeError,'classification response'):n.infer(xs[0])
    def test_timeout_resets_and_recovers(self):
        with device() as n:
            with patch.object(n,'_wait_dma',side_effect=TimeoutError('injected timeout')):
                with self.assertRaises(TimeoutError):n.infer(xs[0])
            self.assertEqual(n.infer(xs[1])['prediction'],int(preds[1]))
    def test_full_reporting_program(self):
        with tempfile.TemporaryDirectory() as out:
            with patch.object(run_lab8,'Lab8NPU',side_effect=lambda *a,**k:device()),patch.object(sys,'argv',['run_lab8.py','--features','--output',out]),contextlib.redirect_stdout(io.StringIO()):
                run_lab8.main()
            summary=json.loads((Path(out)/'summary.json').read_text())
            self.assertEqual(summary['correct'],42);self.assertEqual(summary['feature_values_checked'],6804)
            self.assertEqual(summary['hardware_completed_jobs'],42);self.assertEqual(summary['feature_mismatches'],0)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    (R/('results/python_tests.json' if variant=='lab8_driver' else 'results/python_tests_'+variant+'.json')).write_text(json.dumps({'pass':result.wasSuccessful(),'tests':result.testsRun,'scope':'Host-side driver/program tests with fake transport; not board measurements'},indent=2))
    sys.exit(not result.wasSuccessful())
