from pathlib import Path
import json,re,csv
def resources(p):
 s=p.read_text() if p.exists() else '';d={}
 for key,title in [('lut','Slice LUTs'),('ff','Slice Registers'),('bram','Block RAM Tile'),('dsp','DSPs'),('carry4','CARRY4')]:
  m=re.search(r'\|\s*'+title+r'\*?\s*\|\s*([\d,.]+)',s)
  if m:d[key]=float(m[1].replace(',',''))
 return d
ROOT=Path('/home/ding/vivado_project/Lab6_limit_search')
def row(d):
 r=d/'results';cfg=json.loads((d/'config.json').read_text()) if (d/'config.json').exists() else {};x=dict(name=d.name,source=cfg.get('source'),options=cfg.get('options',{}))
 state=json.loads((r/'run_status.json').read_text()) if (r/'run_status.json').exists() else {}
 for stage in ['sim','synth','impl']:x[stage]=state.get(stage,{}).get('status','not_run');x[stage+'_seconds']=state.get(stage,{}).get('elapsed_seconds')
 log=(r/'sim_console.log').read_text(errors='replace') if (r/'sim_console.log').exists() else ''
 m=re.search(r'SUMMARY correct=(\d+)/42 ties=(\d+) errors=(\d+) values=(\d+) latency_cycles=(\d+)\.\.(\d+) interval_cycles=(\d+)\.\.(\d+)',log)
 if m:
  v=list(map(int,m.groups()));assert v[4]==v[5] and v[6]==v[7];x.update(correct=v[0],ties=v[1],errors=v[2],values=v[3],cycles=v[5],interval_cycles=v[7])
 elif cfg.get('physical_only') or d.name=='postroute_fanout':x.update(cycles=cfg.get('cycles',169),interval_cycles=129,correct=37,ties=0,sim='inherited_RTL')
 x.update(resources(r/('utilization_impl.rpt' if (r/'utilization_impl.rpt').exists() else 'utilization_synth.rpt')))
 if (r/'final_clock.json').exists():
  x.update(json.loads((r/'final_clock.json').read_text()));x.update(latency_ns=round(x['cycles']*x['period'],2),interval_ns=round(x['interval_cycles']*x['period'],2))
  s=(r/'timing_final.rpt').read_text();m=re.search(r'WNS\(ns\).*?\n\s*-+.*?\n\s*([^\n]+)',s,re.S)
  if m:
   v=m[1].split();x.update(tns=float(v[1]),ths=float(v[5]),wpws=float(v[8]),tpws=float(v[9]))
  x['timing_pass']=x['wns']>=0 and x['whs']>=0 and x.get('tns',-1)==0 and x.get('ths',-1)==0 and x.get('wpws',-1)>=0 and x.get('tpws',-1)==0
  m=re.search(r'# of nets with routing errors\.*\s*:\s*(\d+)',(r/'route_status.rpt').read_text());x['route_errors']=int(m[1]) if m else None
  x['improvement_percent']=round(100*(1-x['latency_ns']/801.06),3)
  m=re.search(r'Source:\s*([^\n]+).*?Destination:\s*([^\n]+).*?Data Path Delay:\s*([^\n]+)',s,re.S)
  if m:x.update(critical_source=m[1],critical_destination=m[2],critical_delay=m[3])
 return x
def main():
 plan=json.loads((ROOT/'results/plan.json').read_text());rows=[row(Path(plan['baseline']))]+[row(ROOT/n) for n in plan['candidates']]
 (ROOT/'results/comparison.json').write_text(json.dumps(rows,indent=2))
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with (ROOT/'results/comparison.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 for r in rows:print(r['name'],r['sim'],r['synth'],r['impl'],r.get('period'),r.get('latency_ns'),r.get('lut'),r.get('ff'))
 return rows
if __name__=='__main__':main()
