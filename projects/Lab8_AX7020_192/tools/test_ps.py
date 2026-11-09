"""Host tests for PS packet construction, results and failure handling.
The fake transport checks packets against the independent verified dataset;
this is not a board benchmark or a simulation of the AXI DMA IP.
"""
from pathlib import Path
import sys,unittest,tempfile,json,contextlib,io
from unittest.mock import patch
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'ps'))
from lab8_driver import Lab8NPU
import run_lab8
xs=np.fromfile(R/'ps/inputs.bin',np.int8).reshape(42,512)
gold=np.fromfile(R/'ps/features.bin',np.uint8).reshape(42,162)
preds=np.fromfile(R/'ps/predictions.bin',np.uint8)
class Buffer(np.ndarray):
    def freebuffer(self):self.freed=True
class Registers:
    def __init__(self):self.values={0:0x4c414238,12:142857132,16:0,20:0}
    def read(self,addr):return self.values.get(addr,0)
    def write(self,addr,value):
        if addr==4 and value&1:self.values.update({16:0,20:0,8:0})
class Channel:
    def __init__(self,parent,recv):self.parent=parent;self.recv=recv;self.idle=True;self.running=True;self.error=False;self.transferred=0
    def transfer(self,buf,nbytes):
        self.idle=False
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
    def read(self,addr):return 0
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
    def test_all_course_samples(self):
        with device() as n:
            for i,x in enumerate(xs):
                r=n.infer(x);self.assertEqual(r['prediction'],int(preds[i]));self.assertEqual(r['compute_us'],216*1e6/142857132)
                f=n.features();np.testing.assert_array_equal(np.concatenate([f['fc1'],f['fc2'],f['fc3']]).view(np.uint8),gold[i])
            self.assertEqual(n.regs.read(16),42);self.assertEqual(n.dma.waits,168)
        self.assertTrue(n.tx.freed and n.rx.freed)
    def test_batch_and_buffer_reuse(self):
        with device() as n:
            n.prepare_batch(42)
            tx,rx=n.batch_tx,n.batch_rx
            r=n.infer_batch(xs)
            np.testing.assert_array_equal(r['predictions'],preds)
            np.testing.assert_array_equal(r['scores'].view(np.uint8),gold[:,160:162])
            self.assertEqual(n.dma.waits,2)
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
    (R/'results/python_tests.json').write_text(json.dumps({'pass':result.wasSuccessful(),'tests':result.testsRun,'scope':'Host-side driver/program tests with fake transport; not board measurements'},indent=2))
    sys.exit(not result.wasSuccessful())
