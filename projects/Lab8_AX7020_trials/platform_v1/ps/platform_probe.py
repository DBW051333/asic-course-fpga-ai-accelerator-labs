"""Read-only AX7020 PS clocks, boot identities and model data-movement audit."""
from pathlib import Path
import hashlib,json,time,os,subprocess
import numpy as np
from pynq import MMIO
from lab8_driver import Lab8NPU
R=Path(__file__).resolve().parent
slcr=MMIO(0xF8000000,0x200);offsets=[0x100,0x104,0x108,0x10c,0x120,0x124,0x170,0x1c4]
v={o:slcr.read(o) for o in offsets};ref=33333333.
def pll(o):
 value=v[o];assert not value&0x19
 return ref*((value>>12)&127)
arm_ctrl=v[0x120];arm_src=[0x100,0x100,0x104,0x108][(arm_ctrl>>4)&3];arm_div=(arm_ctrl>>8)&63;assert arm_div>=2
report={'scope':__doc__,'raw_slcr':{hex(k):hex(x) for k,x in v.items()},'reference_hz':ref,'arm_hz':pll(arm_src)/arm_div,'arm_source':hex(arm_src),'arm_divisor':arm_div,'ddr_3x_hz':pll(0x104)/((v[0x124]>>20)&63),'ddr_2x_hz':pll(0x104)/((v[0x124]>>26)&63),'pll_hz':{hex(o):pll(o) for o in [0x100,0x104,0x108]},'loadavg':list(os.getloadavg()),'uname':os.uname()._asdict() if hasattr(os.uname(),'_asdict') else list(os.uname()),'boot_files':{},'api':[],'memory_copy':[],'pass':False}
for f in Path('/boot').iterdir():
 if f.is_file() and f.stat().st_size<100_000_000:report['boot_files'][f.name]={'size':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
report['cpuinfo']=Path('/proc/cpuinfo').read_text();report['meminfo']=Path('/proc/meminfo').read_text();report['cpufreq_available']=Path('/sys/devices/system/cpu/cpu0/cpufreq').exists()
xs=np.fromfile(R/'inputs.bin',np.int8).reshape(42,512);gold=np.fromfile(R/'features.bin',np.int8).reshape(42,162);pred=np.fromfile(R/'predictions.bin',np.uint8)
with Lab8NPU(R/'lab8.bit') as n:
 report['clock']=n.clock_evidence
 for count in [42,128,512,1024,2048,4096]:
  ids=np.arange(count)%42;x=xs[ids].copy();n.prepare_batch(count);rows=[]
  for i in range(110):
   t=time.perf_counter_ns();a=n.infer_batch(x);wall=(time.perf_counter_ns()-t)/1000
   np.testing.assert_array_equal(a['predictions'],pred[ids]);np.testing.assert_array_equal(a['scores'],gold[ids,160:162])
   if i>=10:rows.append({'api_wall_us':wall,**{k:float(a[k]) for k in ['host_dma_window_us','validation_allocation_pack_us','parse_statistics_us','pl_transaction_us','pl_transaction_cycles']}})
  report['api'].append({'N':count,'raw':rows,'medians':{k:float(np.median([row[k] for row in rows])) for k in rows[0]},'buffers':n.buffer_evidence.copy()})
  # Isolate necessary cache maintenance and packing; NOT pure DMA bandwidth.
  stages={k:[] for k in ['send_flush_us','recv_invalidate_us','pack_us']}
  for i in range(110):
   t=time.perf_counter_ns();n.batch_tx.flush();flush=(time.perf_counter_ns()-t)/1000
   t=time.perf_counter_ns();n.batch_rx.invalidate();invalidate=(time.perf_counter_ns()-t)/1000
   t=time.perf_counter_ns();n._batch_tx_bytes[8:8+count*512]=x.view(np.uint8).reshape(-1);pack=(time.perf_counter_ns()-t)/1000
   if i>=10:stages['send_flush_us'].append(flush);stages['recv_invalidate_us'].append(invalidate);stages['pack_us'].append(pack)
  report['api'][-1]['maintenance']={k:{'median':float(np.median(values)),'raw':values} for k,values in stages.items()}
  print('PASS N',count,report['api'][-1]['medians'],flush=True)
 assert n.regs.read(0x14)==0
# CPU numpy copy is not a PL DMA benchmark.
for size in [1<<20,8<<20,32<<20]:
 a=np.arange(size,dtype=np.uint8);b=np.empty_like(a);rows=[]
 for i in range(30):
  t=time.perf_counter_ns();b[:]=a;elapsed=(time.perf_counter_ns()-t)*1e-9
  if i>=5:rows.append(size/elapsed/1e6)
 np.testing.assert_array_equal(a,b);report['memory_copy'].append({'bytes':size,'payload_MB_per_s':float(np.median(rows)),'raw_MB_per_s':rows,'scope':'CPU cached NumPy payload copy, not DDR or DMA bandwidth'})
report['pass']=True;(R/'platform_probe.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS PS/DDR AUDIT')
