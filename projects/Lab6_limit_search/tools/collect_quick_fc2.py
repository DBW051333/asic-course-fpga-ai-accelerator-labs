from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).parent))
from collect import row
root=Path('/home/ding/vivado_project/Lab6_limit_search')
base=json.loads((root/'results/recommended.json').read_text())
rows=[row(root/name) for name in ['quick_fc2_rom_pipe','quick_fc2_keep_weight']]
for item in rows:
 if 'latency_ns' in item:
  item.pop('improvement_percent',None)
  item['gain_vs_741_2_percent']=round(100*(1-item['latency_ns']/741.2),3)
result={'baseline':base,'trials':rows,'scope':'48 overlapping RTL requests; routed static timing; no gate-level or board test'}
(root/'results/quick_fc2_results.json').write_text(json.dumps(result,indent=2))
for item in rows:print(json.dumps(item,ensure_ascii=False))
