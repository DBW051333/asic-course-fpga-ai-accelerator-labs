import sys,json,csv,re
from pathlib import Path
sys.path.insert(0,'/home/ding/vivado_project/Lab6_limit_search/tools')
from collect import row
root=Path('/home/ding/vivado_project/Lab6_architecture_trials')
plan=json.loads((root/'results/plan.json').read_text())
rows=[row(Path(plan['baseline']))]+[row(root/n) for n in plan['candidates']]
for r in rows:
 r.pop('improvement_percent',None)
 if 'latency_ns' in r:r['gain_vs_735_3_percent']=round(100*(1-r['latency_ns']/735.3),3)
 if r['name']=='fc2_interleaved_split11':
  log=(root/r['name']/'results/final_verify_console.log').read_text()
  r['final_clock_rtl_and_reopened_dcp_verified']='PASS: 48 overlapping' in log and 'errors=0' in log and 'ERROR:' not in log and 'Exiting Vivado' in log
(root/'results/comparison.json').write_text(json.dumps(rows,indent=2))
fields=list(dict.fromkeys(k for r in rows for k in r))
with (root/'results/comparison.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
best=rows[-1]
assert best['timing_pass'] and best['route_errors']==0 and best['final_clock_rtl_and_reopened_dcp_verified']
(root/'results/selected.json').write_text(json.dumps(best,indent=2))
for r in rows: print(r['name'],r['impl'],r.get('latency_ns'),r.get('gain_vs_735_3_percent'))
lines=['| 版本 | 拍数 | 最终周期 ns | 延迟 ns | 启动间隔 ns | LUT / FF | BRAM / DSP | 相对原版延迟 |','|---|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
 lines.append(f"| {r['name']} | {r['cycles']} | {r.get('period','实现中')} | {r.get('latency_ns','待定')} | {r.get('interval_ns','待定')} | {int(r['lut'])} / {int(r['ff'])} | {int(r['bram'])} / {int(r['dsp'])} | {r.get('gain_vs_735_3_percent','待定')}% 缩短 |")
(root/'results/table.md').write_text('\n'.join(lines))
