from pathlib import Path
import json
ROOT=Path('/home/ding/vivado_project/Lab6_limit_search');src=ROOT/'phys_aggressive45';p=ROOT/'results/plan.json';plan=json.loads(p.read_text())
for name,directive in [('phys_aggressive43','AggressiveExplore'),('phys_fanout43','AggressiveFanoutOpt')]:
 d=ROOT/name;(d/'tools').mkdir(parents=True,exist_ok=True);(d/'results').mkdir(exist_ok=True)
 s=(src/'tools/run_impl.tcl').read_text().replace(str(src),str(d))
 # The input is the already improved 4.58 ns checkpoint; reports stay isolated.
 s=s.replace('/home/ding/vivado_project/Lab6_bottleneck_optimization/postroute_fanout/results/final_routed.dcp',str(src/'results/final_routed.dcp'))
 s=s.replace('create_clock -period 4.5','create_clock -period 4.3').replace('phys_opt_design -directive AggressiveExplore',f'phys_opt_design -directive {directive}')
 (d/'tools/run_impl.tcl').write_text(s)
 cfg=json.loads((src/'config.json').read_text());cfg.update(name=name,physical_source=str(src),change=f'Iterative {directive} at 4.3 ns target');(d/'config.json').write_text(json.dumps(cfg,indent=2));plan['candidates'].append(name)
p.write_text(json.dumps(plan,indent=2))
print('Prepared two next-round physical probes at a tighter target')
