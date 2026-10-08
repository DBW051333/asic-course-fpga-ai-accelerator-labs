from pathlib import Path
import json,tarfile,re,csv
R=Path(__file__).resolve().parent;items=json.loads((R/'versions.json').read_text());rows=[]
for x in items:
 measures=[]
 with tarfile.open(R/x['archive'],'r:gz') as t:
  for m in t.getmembers():
   if not m.name.endswith('.rpt'):continue
   s=t.extractfile(m).read().decode(errors='ignore');data={'version':x['version'],'report':m.name,'design_state':next(iter(re.findall(r'Design State\s*:\s*([^\n]+)',s)),'unknown').strip()}
   for key,label in [('lut','Slice LUTs'),('ff','Slice Registers'),('bram','Block RAM Tile'),('dsp','DSPs'),('carry4','CARRY4')]:
    match=re.search(r'^\|\s*'+label+r'\s*\*?\s*\|\s*([\d.,]+)',s,re.M)
    if match:data[key]=float(match.group(1).replace(',',''))
   match=re.search(r'^\s*WNS\(ns\).*\n\s*[- ]+\n\s*([-\d.]+)\s+([-\d.]+)\s+(\d+)\s+(\d+)\s+([-\d.]+)\s+([-\d.]+)\s+(\d+)\s+(\d+)\s+([-\d.]+)\s+([-\d.]+)',s,re.M)
   if match:
    names=['wns','tns','setup_failing_endpoints','setup_endpoints','whs','ths','hold_failing_endpoints','hold_endpoints','wpws','tpws'];data.update({k:float(v) for k,v in zip(names,match.groups())})
   match=re.search(r'^\s*\S+\s+\{[\d. ]+\}\s+([\d.]+)\s+([\d.]+)',s,re.M)
   if match:data['period_ns']=float(match.group(1));data['frequency_mhz']=float(match.group(2))
   if len(data)>3:measures.append(data);rows.append(data)
 x['report_measurements']=measures
 # Fill structured summary gaps from the designated routed report, retaining provenance.
 for preferred in ['results/timing_verified.rpt','results/timing_final.rpt','experiment_results/timing_impl.rpt','results/timing_impl.rpt','results/utilization_impl.rpt','experiment_results/utilization_impl.rpt']:
  for d in measures:
   if d['report']!=preferred:continue
   for k,v in d.items():
    if k in {'version','report','design_state'}:continue
    metric='period' if k=='period_ns' else k
    if metric not in x['reported_metrics']:x['reported_metrics'][metric]=v
   x.setdefault('summary_report_sources',[]).append(d['report'])
(R/'versions.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
cols=sorted({k for r in rows for k in r})
with (R/'report_measurements.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
cols=['version','keep_project','sim','synth','impl','cycles','interval_cycles','period','latency_ns','lut','ff','bram','dsp','wns','whs','archive','recorded_files']
with (R/'versions.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for x in items:
  row={k:x.get(k,'') for k in cols};row.update({k:x['reported_metrics'].get(k,'') for k in cols if k not in x});w.writerow(row)
print('Indexed',len(rows),'report measurements from',len(items),'versions')
