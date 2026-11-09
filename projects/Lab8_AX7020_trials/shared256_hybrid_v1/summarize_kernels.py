from pathlib import Path
import json,re
R=Path(__file__).resolve().parent
assert 'PASS 16744448 triples plus randomized CE stalls' in (R/'mul_test/result.log').read_text()
out={'scope':'36 independent packed25/24x8 lanes, registered common inputs/outputs; three CE-enabled multiplier cycles, II=1; routed OOC register-to-register timing only; 7ns xc7z020clg400-2','correctness':{'triples':16744448,'weight_domain':'all signed INT8 weight pairs whose B=65536*w1+w0 fits signed24','activation_domain':'all signed INT8','random_ce_stalls':True,'pass':True},'kernels':{}}
for name in ['generic25','booth24','packed_sparse']:
 p=R/'kernels'/name/'results';s=(p/'routed_utilization.rpt').read_text()
 m={k:int(re.search(r'\| '+label+r'\s*\|\s*([0-9]+)',s).group(1)) for k,label in [('lut','Slice LUTs'),('ff','Slice Registers'),('dsp','DSPs'),('carry4','CARRY4')]}
 lines=dict(x.split(maxsplit=1) for x in (p/'routed_metrics.txt').read_text().splitlines());m.update(wns_ns=float(lines['max']),whs_ns=float(lines['min']),unrouted=int(lines['UNROUTED']),route_errors=int(lines['ROUTE_ERRORS']))
 assert m['dsp']==0 and m['wns_ns']>=0 and m['whs_ns']>=0 and m['unrouted']==0 and m['route_errors']==0
 out['kernels'][name]=m
out['selected']='packed_sparse';out['lut_saving_vs_generic_percent']=(1-out['kernels']['packed_sparse']['lut']/out['kernels']['generic25']['lut'])*100
out['lut_saving_vs_booth24_percent']=(1-out['kernels']['packed_sparse']['lut']/out['kernels']['booth24']['lut'])*100
(R/'kernel_comparison.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
