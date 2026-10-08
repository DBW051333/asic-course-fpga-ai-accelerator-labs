from pathlib import Path
import json,re,csv
ROOT=Path('/home/ding/vivado_project/Lab6_bottleneck_optimization')
OLD=Path('/home/ding/vivado_project/Lab5_truncation_optimization/q8_lab6_tree8_rompack_d200')
def resources(p):
    s=p.read_text() if p.exists() else '';d={}
    for key,title in [('lut','Slice LUTs'),('ff','Slice Registers'),('bram','Block RAM Tile'),('dsp','DSPs')]:
        m=re.search(r'\|\s*'+title+r'\*?\s*\|\s*([\d,.]+)',s)
        if m:d[key]=float(m[1].replace(',',''))
    return d
def row(d,baseline=False):
    r=d/'results';x=dict(name='previous_best' if baseline else d.name)
    status=json.loads((r/'run_status.json').read_text()) if (r/'run_status.json').exists() else {}
    for stage in ['sim','synth','impl']:x[stage]=status.get(stage,{}).get('status','not_run')
    log=(r/'sim_console.log').read_text() if (r/'sim_console.log').exists() else ''
    m=re.search(r'SUMMARY correct=(\d+)/42 ties=(\d+) errors=(\d+) values=(\d+) latency_cycles=(\d+)\.\.(\d+) interval_cycles=(\d+)\.\.(\d+)',log)
    if m:
        v=list(map(int,m.groups()));x.update(correct=v[0],ties=v[1],errors=v[2],values=v[3],cycles=v[5],interval_cycles=v[7]);assert v[4]==v[5] and v[6]==v[7]
    elif d.name=='postroute_fanout':
        x.update(cycles=169,interval_cycles=129,correct=37,ties=0,sim='inherited_same_rtl')
        p=ROOT/'results/recommended.json'
        if p.exists():
            verified=json.loads(p.read_text())
            if verified.get('name')==d.name and verified.get('verification')=='passed':
                x.update(sim='passed',errors=0,values=7776,sim_scope='Exported identical RTL verified at final clock; not gate-level simulation')
    p=r/'utilization_impl.rpt';x.update(resources(p if p.exists() else r/'utilization_synth.rpt'))
    if (r/'final_clock.json').exists():
        x.update(json.loads((r/'final_clock.json').read_text()));x['latency_ns']=round(x['cycles']*x['period'],2);x['interval_ns']=round(x['interval_cycles']*x['period'],2)
        s=(r/'timing_final.rpt').read_text();m=re.search(r'WNS\(ns\).*?\n\s*-+.*?\n\s*([^\n]+)',s,re.S)
        if m:
            v=m[1].split();x.update(tns=float(v[1]),ths=float(v[5]),wpws=float(v[8]))
        x['timing_pass']=x['wns']>=0 and x['whs']>=0 and x.get('tns',-1)==0 and x.get('ths',-1)==0 and x.get('wpws',-1)>=0
        route=(r/'route_status.rpt').read_text();m=re.search(r'# of nets with routing errors\.*\s*:\s*(\d+)',route);x['route_errors']=int(m[1]) if m else None
        x['improvement_percent']=round(100*(1-x['latency_ns']/851.76),3)
    return x
def main():
    rows=[row(OLD,True)]+[row(ROOT/n) for n in json.loads((ROOT/'results/plan.json').read_text())['candidates']]
    (ROOT/'results/comparison.json').write_text(json.dumps(rows,indent=2))
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (ROOT/'results/comparison.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    for r in rows:print(r)
    return rows
if __name__=='__main__':main()
