from pathlib import Path
import re,json
r=Path('/home/ding/vivado_project/Lab5_optimization');rows=[]
for d in sorted(r.glob('stream*')):
 p=d/'results/timing_impl.rpt'
 if not p.exists():continue
 fcfile=d/'results/final_clock.json'
 if fcfile.exists() and json.loads(fcfile.read_text()).get('implementation_run')=='impl_explore':p=d/'results/timing_explore.rpt'
 s=p.read_text();m=re.search(r'\n\s*(-?[\d.]+)\s+(-?[\d.]+)\s+\d+\s+\d+\s+(-?[\d.]+)\s+(-?[\d.]+)\s+\d+\s+\d+\s+(-?[\d.]+)',s)
 timing=dict(zip(['wns','tns','whs','ths','wpws'],map(float,m.groups()))) if m else {}
 u=(d/'results/utilization_impl.rpt').read_text();util={}
 for key,pat in [('lut',r'\| Slice LUTs\*?\s*\|\s*([\d.]+)'),('ff',r'\| Slice Registers\s*\|\s*([\d.]+)'),('bram',r'\| Block RAM Tile\s*\|\s*([\d.]+)'),('dsp',r'\| DSPs\s*\|\s*([\d.]+)')]:
  mm=re.search(pat,u);util[key]=float(mm.group(1)) if mm else None
 x=(d/'timing.xdc').read_text();period=float(re.search(r'-period\s+([\d.]+)',x).group(1))
 sim=d/'results/sim_console.log';cycles=None
 if sim.exists():
  mm=re.search(r'MEASURE job=0 .*cycles=(\d+)',sim.read_text());cycles=int(mm.group(1)) if mm else None
 if cycles is None and sim.exists():
  mm=re.search(r'MEASURE job=0 elapsed_ns=(\d+)',sim.read_text());cycles=int(mm.group(1))//10 if mm else None
 if cycles is None:
  base=d.name.split('_clk')[0];sp=r/base/'results/sim_console.log'
  if sp.exists():
   mm=re.search(r'MEASURE job=0 .*cycles=(\d+)',sp.read_text());cycles=int(mm.group(1)) if mm else None
 row=dict(name=d.name,period=period,cycles=cycles,latency_ns=cycles*period if cycles else None,**timing,**util)
 f=d/'results/final_clock.json'
 if f.exists():
  fc=json.loads(f.read_text());row['final_period']=fc['period'];row['final_wns']=fc['wns'];row['final_whs']=fc['whs'];row['final_latency_ns']=cycles*fc['period'] if cycles else None
 rows.append(row)
(r/'results/all_results.json').write_text(json.dumps(rows,indent=2))
for x in rows:print(x)
