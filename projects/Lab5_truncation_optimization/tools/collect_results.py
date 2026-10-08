#!/usr/bin/env python3
from pathlib import Path
import csv,json,re
from search_quantization import ROOT,BASE,X,infer

def resource(path):
    if not path.exists():return {}
    s=path.read_text();d={}
    for field,title in [('lut','Slice LUTs'),('ff','Slice Registers'),('bram','Block RAM Tile'),('dsp','DSPs')]:
        m=re.search(r'\|\s*'+re.escape(title)+r'\*?\s*\|\s*([\d,.]+)',s)
        if m:d[field]=float(m[1].replace(',',''))
    return d

def collect():
    cs=json.loads((ROOT/'results/candidates.json').read_text());rows=[]
    for c in cs:
        d=ROOT/c['name'];r=d/'results';status=json.loads((r/'run_status.json').read_text()) if (r/'run_status.json').exists() else {}
        m=dict(c);m['sim_status']=status.get('sim',{}).get('status','not_run')
        s=(r/'sim_console.log').read_text(errors='replace') if (r/'sim_console.log').exists() else ''
        match=re.search(r'SUMMARY correct=(\d+)/42 ties=(\d+) errors=(\d+) values=(\d+) latency_cycles=(\d+)\.\.(\d+) interval_cycles=(\d+)\.\.(\d+)',s)
        if match:
            a=list(map(int,match.groups()));m.update(rtl_correct=a[0],rtl_ties=a[1],errors=a[2],values=a[3],cycles=a[5],interval_cycles=a[7])
            if 'PASS: 48 overlapping' in s:m['sim_status']='passed'
            assert a[0]==c['correct'] and a[1]==c['ties'] and a[2]==0 and a[3]==7776
            assert a[4]==a[5] and a[6]==a[7]
        m['synth_status']=status.get('synth',{}).get('status','not_run')
        m['impl_status']=status.get('impl',{}).get('status','not_run')
        m['synth_resources']=resource(r/'utilization_synth.rpt')
        m['resources']=resource(r/'utilization_impl.rpt') if m['impl_status']=='passed' else m['synth_resources']
        for stage in ['sim','synth','impl']:m[stage+'_elapsed_seconds']=status.get(stage,{}).get('elapsed_seconds')
        if m['impl_status']=='passed':
            clk=json.loads((r/'final_clock.json').read_text());m.update(clk)
            report=(r/'timing_final.rpt').read_text()
            line=re.search(r'WNS\(ns\).*?\n\s*-+.*?\n\s*([^\n]+)',report,re.S)
            if line:
                vals=line.group(1).split()
                m['wpws']=float(vals[8]);m['ths']=float(vals[5]);m['tns']=float(vals[1])
            m['physical_pass']=clk['wns']>=0 and clk['whs']>=0 and m.get('wpws',-1)>=0 and m.get('ths',-1)==0
            m['latency_ns']=round(m['cycles']*clk['period'],3)
            m['interval_ns']=round(m['interval_cycles']*clk['period'],3)
            m['speedup_vs_baseline']=round(883.68/m['latency_ns'],4)
            m['latency_reduction_percent']=round((1-m['latency_ns']/883.68)*100,3)
        qlayers,_,_=infer(X,c['widths'],c['shifts'],c['mode'],c.get('product_cut',0))
        m['sample0_layers']=[x[0].tolist() for x in qlayers]
        if c.get('product_cut'):
            standard,_,_=infer(X,c['widths'],c['shifts'],c['mode'])
            m['layer_max_error_vs_layer_only']=[int(abs(a-b).max()) for a,b in zip(qlayers,standard)]
            m['layer_mean_abs_error_vs_layer_only']=[float(abs(a-b).mean()) for a,b in zip(qlayers,standard)]
            m['fc1_worst_case_product_error_bound']=512*(1<<(c['product_cut']-1))
        rows.append(m)
    (ROOT/'results/hardware_comparison.json').write_text(json.dumps(rows,indent=2))
    fields=['name','widths','shifts','mode','product_cut','product_cut_stage','tree_stages','dsp1','tail','correct','ties','disagreements','overflow_counts',
            'sim_status','synth_status','impl_status','cycles','interval_cycles','period','wns','whs','wpws','physical_pass',
            'latency_ns','interval_ns','speedup_vs_baseline','lut','ff','bram','dsp','sim_elapsed_seconds','synth_elapsed_seconds','impl_elapsed_seconds']
    with (ROOT/'results/hardware_comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader()
        for m in rows:w.writerow(dict(m,**m['resources']))
    for m in rows:print(m['name'],m['sim_status'],m['synth_status'],m['impl_status'],m.get('period'),m['resources'])
    return rows

if __name__=='__main__':collect()
