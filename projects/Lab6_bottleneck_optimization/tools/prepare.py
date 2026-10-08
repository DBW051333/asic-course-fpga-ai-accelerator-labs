from pathlib import Path
import json, shutil

ROOT=Path('/home/ding/vivado_project/Lab6_bottleneck_optimization')
OLD=Path('/home/ding/vivado_project/Lab5_truncation_optimization')
BASE=OLD/'q8_lab6_tree8_rompack_d200'
names=['terminal_tree8','terminal_tree7']
for name in names:
    src=BASE if name.endswith('8') else OLD/'q8_lab6_rompack_d200'
    d=ROOT/name
    d.mkdir(exist_ok=True)
    for sub in ['rtl','data','tb','tools']:
        shutil.copytree(src/sub,d/sub,dirs_exist_ok=True)
        for p in (d/sub).glob('*'):
            if p.is_file() and p.suffix in ['.v','.tcl']:
                p.write_text(p.read_text().replace(str(src),str(d)))
    (d/'results').mkdir(exist_ok=True)
    shutil.copy2(src/'timing.xdc',d/'timing.xdc')
    p=d/'rtl/fc1_paired.v';s=p.read_text()
    s=s.replace('reg [7:0] issue_addr;', 'localparam ADDRESS_WIDTH=$clog2(64*GROUPS);\n reg last_issue;reg [ADDRESS_WIDTH-1:0] issue_addr;')
    s=s.replace('running<=0;issue_addr<=0;', 'running<=0;last_issue<=0;issue_addr<=0;')
    s=s.replace('running<=1;issue_addr<=0;', 'running<=1;last_issue<=0;issue_addr<=0;')
    s=s.replace('if(issue_addr==64*GROUPS-1)running<=0;', 'last_issue<=last_issue || (issue_addr==64*GROUPS-2);if(last_issue)running<=0;')
    assert 'reg last_issue;' in s and 'if(last_issue)' in s
    p.write_text(s)
    cfg=json.loads((src/'config.json').read_text());cfg.update(name=name,source=str(src),change='Registered terminal-count lookahead; minimal legal ROM address width; no added pipeline stage')
    (d/'config.json').write_text(json.dumps(cfg,indent=2))
    p=d/'tools/run_synth.tcl';p.write_text(p.read_text().replace(src.name,name))

# A quick physical-only experiment starts from the already routed design.
d=ROOT/'postroute_fanout';(d/'results').mkdir(parents=True,exist_ok=True);(d/'tools').mkdir(exist_ok=True)
s=(BASE/'tools/run_impl.tcl').read_text()
begin=s.index(' report_utilization')
tail=s[begin:].replace(str(BASE),str(d))
s=f'''set_param general.maxThreads 8
open_checkpoint {BASE}/results/final_routed.dcp
create_clock -period 4.8 [get_ports clk_i]
phys_opt_design -directive AggressiveFanoutOpt
route_design -directive Explore
'''+tail
(d/'tools/run_impl.tcl').write_text(s)
(d/'config.json').write_text(json.dumps(dict(name=d.name,source=str(BASE),change='Post-route AggressiveFanoutOpt and incremental reroute',cycles=169,interval_cycles=129),indent=2))
(ROOT/'results/plan.json').write_text(json.dumps(dict(baseline=str(BASE),candidates=names+['postroute_fanout']),indent=2))
print('Prepared two focused RTL candidates and one physical-only trial')
