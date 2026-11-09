"""Real DMA timeout/internal-error injection with recovery; no invalid addresses."""
from pathlib import Path
import hashlib,json,time
from unittest.mock import patch
import numpy as np
from lab8_driver import Lab8NPU
R=Path(__file__).resolve().parent
xs=np.fromfile(R/'inputs.bin',np.int8).reshape(42,512);pred=np.fromfile(R/'predictions.bin',np.uint8);gold=np.fromfile(R/'features.bin',np.int8).reshape(42,162)
report={'pass':False,'driver_sha256':hashlib.sha256((R/'lab8_driver.py').read_bytes()).hexdigest(),'phases':[]}
def save():(R/'dma_fault_results.json').write_text(json.dumps(report,indent=2)+'\n')
try:
 with Lab8NPU(R/'lab8.bit',timeout=.05) as n:
  report['clock']=n.clock_evidence
  def recover():
   v=n.infer_batch(xs);np.testing.assert_array_equal(v['predictions'],pred);np.testing.assert_array_equal(v['scores'],gold[:,160:162]);assert n.regs.read(0x14)==0
  recover();wait=n._wait_dma
  def capture():
   try:wait()
   except Exception:
    report['last_fault_status']={'send':hex(n.dma.mmio.read(4)),'recv':hex(n.dma.mmio.read(0x34))};raise
  with patch.object(n,'_wait_dma',side_effect=capture):
   # Arm the actual receive engine but deliberately withhold send.
   started=time.monotonic()
   try:
    with patch.object(n.dma.sendchannel,'transfer',return_value=None):n._exchange(8,168)
   except TimeoutError as e:
    report['phases'].append({'name':'real_receive_pending_timeout','pass':True,'exception':str(e),'elapsed_seconds':time.monotonic()-started,'status_before_reset':report['last_fault_status']})
   else:raise AssertionError('pending receive did not time out')
   recover();save()
   # Feature response is 162 bytes; physically allocated rx is 168 bytes.
   # Advertise only 8 bytes to S2MM to provoke its length Internal Error.
   n._tx_bytes[:8]=np.frombuffer((2).to_bytes(8,'little'),np.uint8)
   try:n._exchange(8,8)
   except RuntimeError as e:
    status=report['last_fault_status'];assert int(status['recv'],16)&0x70
    report['phases'].append({'name':'real_s2mm_length_error','pass':True,'exception':str(e),'status_before_reset':status,'physical_rx_capacity':n.rx.nbytes,'advertised_receive_bytes':8,'packet_bytes':162})
   else:raise AssertionError('S2MM length error was not detected')
   recover();save()
 report['pass']=True;save();print('PASS REAL DMA TIMEOUT/ERROR AND RECOVERY')
except Exception as e:report['failure']=repr(e);save();raise
