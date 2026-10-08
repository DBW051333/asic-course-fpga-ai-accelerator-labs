from pathlib import Path
import json,shutil
ROOT=Path('/home/ding/vivado_project/Lab6_limit_search')
OLD=Path('/home/ding/vivado_project/Lab6_bottleneck_optimization')
SRC=Path('/home/ding/vivado_project/Lab5_truncation_optimization/q8_lab6_tree8_rompack_d200')
variants={
 'bram_pipe':dict(pipe=True),
 'narrow':dict(narrow=True),
 'bram_pipe_narrow':dict(pipe=True,narrow=True),
 'free_address_narrow':dict(free=True,narrow=True),
 'free_address_pipe_narrow':dict(free=True,pipe=True,narrow=True),
 'fc1_prepack_pipe_narrow':dict(prepack=True,pipe=True,narrow=True,free=True),
}
for name,options in variants.items():
 d=ROOT/name;d.mkdir(exist_ok=True)
 for sub in ['rtl','tb','tools','data']:
  shutil.copytree(SRC/sub,d/sub,dirs_exist_ok=True)
  for p in (d/sub).glob('*'):
   if p.suffix in ['.v','.tcl']:p.write_text(p.read_text().replace(str(SRC),str(d)).replace(SRC.name,name))
 (d/'results').mkdir(exist_ok=True);shutil.copy2(SRC/'timing.xdc',d/'timing.xdc')
 p=d/'rtl/fc1_paired.v';s=p.read_text()
 if options.get('pipe'):
  s=s.replace('reg [LANES*16-1:0] weight_r;reg [LANES*8-1:0] input_r;', 'reg [LANES*16-1:0] weight_r,weight_q;reg [LANES*8-1:0] input_r,input_q;')
  s=s.replace('weight_r[','weight_q[').replace('input_p[j]<=input_r[','input_p[j]<=input_q[')
  s=s.replace('weight_r<=weights[issue_addr];input_r<=inputs[issue_group];','weight_r<=weights[issue_addr];weight_q<=weight_r;input_r<=inputs[issue_group];input_q<=input_r;')
  s=s.replace('reg [14:0] valid_pipe;reg [7:0] tag[0:14];','reg [15:0] valid_pipe;reg [7:0] tag[0:15];')
  s=s.replace('tag[14]','tag[15]').replace('valid_pipe[14]','valid_pipe[15]').replace('valid_pipe[13:0]','valid_pipe[14:0]').replace('j<15','j<16')
 if options.get('free'):
  s=s.replace('reg [7:0] issue_addr;','reg [$clog2(64*GROUPS)-1:0] issue_addr;')
  s=s.replace('always @(posedge clk_i) begin\n  weight_r', "always @(posedge clk_i) begin\n  // Invalid cycles may read any legal address; valid_pipe gates all accumulation.\n  issue_addr<=issue_addr+1'b1;\n  weight_r")
  s=s.replace("if(issue_addr==64*GROUPS-1)running<=0;else issue_addr<=issue_addr+1'b1;","if(issue_addr==64*GROUPS-1)running<=0;")
 if options.get('prepack'):
  raw=[int(v,16) for v in Path('/home/ding/vivado_project/Lab5_optimization/data/stream_pair256_hybrid_weights.mem').read_text().split()]
  packed=[]
  for row in raw:
   out=0
   for g in range(256):
    v=(row>>((255-g)*16))&65535;w0=v&255;w1=v>>8
    w0=w0-256 if w0>=128 else w0;w1=w1-256 if w1>=128 else w1
    v=(((w1<<16)+w0)&((1<<25)-1)) if g<200 else (v<<9)
    out=(out<<25)|v
   packed.append(f'{out:01600x}')
  (d/'data/fc1_prepacked.mem').write_text('\n'.join(packed)+'\n')
  s=s.replace('LANES*16-1:0] weights','LANES*25-1:0] weights').replace('LANES*16-1:0] weight_r','LANES*25-1:0] weight_r')
  lines=s.splitlines()
  for i,line in enumerate(lines):
   if 'packed_w[j]<=' in line:lines[i]='   packed_w[j]<=weight_q[LANES*25-1-j*25 -:25];'
   elif 'w0_p[j]<=' in line:lines[i]=line.replace('LANES*16','LANES*25').replace('j*16','j*25')
  s='\n'.join(lines)+'\n'
  tp=d/'rtl/lab5_top.v';tp.write_text(tp.read_text().replace('/home/ding/vivado_project/Lab5_optimization/data/stream_pair256_hybrid_weights.mem',str(d/'data/fc1_prepacked.mem')))
 p.write_text(s)
 if options.get('narrow'):
  p=d/'rtl/lab5_top.v';s=p.read_text().replace('.AW(23),.OW(23)', '.AW(21),.OW(23)').replace('.AW(21),.OW(21)', '.AW(19),.OW(21)');p.write_text(s)
 # Use fewer synthesis workers to avoid the previously observed memory pressure.
 p=d/'tools/run_synth.tcl';p.write_text(p.read_text().replace('general.maxThreads 4','general.maxThreads 2'))
 p=d/'tools/run_impl.tcl';s=p.read_text().replace(' report_utilization -file',' phys_opt_design -directive AggressiveFanoutOpt\n route_design -directive Explore\n report_utilization -file',1);p.write_text(s)
 cfg=json.loads((SRC/'config.json').read_text());cfg.update(name=name,source=str(SRC),options=options,cycles=170 if options.get('pipe') else 169,interval_cycles=129)
 (d/'config.json').write_text(json.dumps(cfg,indent=2))
# Targeted physical BRAM-register optimization on the currently best routed DCP.
name='phys_bram_register';d=ROOT/name;(d/'tools').mkdir(parents=True,exist_ok=True);(d/'results').mkdir(exist_ok=True)
s=(OLD/'postroute_fanout/tools/run_impl.tcl').read_text().replace(str(OLD/'postroute_fanout'),str(d))
s=s.replace(str(SRC/'results/final_routed.dcp'),str(OLD/'postroute_fanout/results/final_routed.dcp')).replace('create_clock -period 4.8','create_clock -period 4.5').replace('phys_opt_design -directive AggressiveFanoutOpt','phys_opt_design -bram_register_opt -dsp_register_opt -critical_pin_opt -routing_opt')
(d/'tools/run_impl.tcl').write_text(s)
(d/'config.json').write_text(json.dumps(dict(name=name,source=str(SRC),physical_source=str(OLD/'postroute_fanout'),cycles=169,interval_cycles=129,physical_only=True),indent=2))
(ROOT/'results/plan.json').write_text(json.dumps(dict(baseline=str(OLD/'postroute_fanout'),baseline_latency_ns=801.06,clear_gain_percent=1.0,candidates=list(variants)+[name]),indent=2))
(ROOT/'results/research.json').write_text(json.dumps(dict(sources=[dict(url='https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Performance-Considerations-When-Implementing-RAM',use='Same-hierarchy BRAM output pipeline and address pipeline'),dict(url='https://docs.amd.com/r/2025.2-English/ug835-vivado-tcl-commands/phys_opt_design',use='BRAM/DSP register movement, retiming, iterative post-route optimization')]),indent=2))
print('Prepared six RTL variants and one targeted physical trial')
