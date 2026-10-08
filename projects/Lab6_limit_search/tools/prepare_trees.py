from pathlib import Path
import json,shutil,math
ROOT=Path('/home/ding/vivado_project/Lab6_limit_search');src=ROOT/'free_biaspipe_narrow'
plan=json.loads((ROOT/'results/plan.json').read_text())
for name,radices in [('ternary6_bias_narrow',[3]*6),('hybrid7_bias_narrow',[3,3,2,2,2,2,2])]:
 d=ROOT/name;d.mkdir(exist_ok=True)
 for sub in ['rtl','data','tb','tools']:
  shutil.copytree(src/sub,d/sub,dirs_exist_ok=True)
  for p in (d/sub).glob('*'):
   if p.suffix in ['.v','.tcl']:p.write_text(p.read_text().replace(str(src),str(d)).replace(src.name,name))
 (d/'results').mkdir(exist_ok=True);shutil.copy2(src/'timing.xdc',d/'timing.xdc')
 lines=['module adder_tree(input wire clk,rst_n,input wire [4095:0] data,output wire [31:0] sum_out);','wire signed [15:0] p[0:255];','genvar i;generate for(i=0;i<256;i=i+1)begin:leaf assign p[i]=$signed(data[4095-i*16 -:16]);end endgenerate']
 n=256;width=16;fanin=1;prev='p';proof=[]
 for level,radix in enumerate(radices):
  nxt=math.ceil(n/radix);fanin=min(256,fanin*radix);nw=16+math.ceil(math.log2(fanin))
  lines.append(f'reg signed [{nw-1}:0] s{level}[0:{nxt-1}];')
  for j in range(nxt):
   terms=[]
   for k in range(radix):
    idx=j*radix+k
    if idx<n:terms.append('{{'+str(nw-width)+'{'+prev+f'[{idx}][{width-1}]'+'}},'+prev+f'[{idx}]'+'}')
   lines.append(f'always @(posedge clk)s{level}[{j}] <= '+' + '.join(terms)+';')
  proof.append(dict(level=level,radix=radix,nodes=nxt,width=nw,maximum_leaves=fanin,minimum=fanin*(-32768),maximum=fanin*32767))
  assert -(1<<(nw-1))<=proof[-1]['minimum'] and proof[-1]['maximum']<(1<<(nw-1))
  n=nxt;width=nw;prev=f's{level}'
 assert n==1
 lines.append('assign sum_out={{'+str(32-width)+'{'+prev+f'[0][{width-1}]'+'}},'+prev+'[0]};endmodule')
 (d/'rtl/adder_tree.v').write_text('\n'.join(lines)+'\n')
 # Product and memory pipeline has seven stages; the tree changes only this tail.
 last=6+len(radices);p=d/'rtl/fc1_paired.v';s=p.read_text()
 s=s.replace('[14:0] valid_pipe',f'[{last}:0] valid_pipe').replace('tag[0:14]',f'tag[0:{last}]').replace('bias_pipe[0:14]',f'bias_pipe[0:{last}]')
 s=s.replace('tag[14]',f'tag[{last}]').replace('bias_pipe[14]',f'bias_pipe[{last}]').replace('valid_pipe[14]',f'valid_pipe[{last}]').replace('valid_pipe[13:0]',f'valid_pipe[{last-1}:0]').replace('j<15',f'j<{last+1}').replace('bi<15',f'bi<{last+1}')
 p.write_text(s)
 cfg=json.loads((src/'config.json').read_text());cfg.update(name=name,source=str(src),cycles=169+len(radices)-8,tree_stages=len(radices));cfg['options']['radices']=radices
 (d/'config.json').write_text(json.dumps(cfg,indent=2));(d/'data/tree_width_proof.json').write_text(json.dumps(proof,indent=2));plan['candidates'].append(name)
(ROOT/'results/plan.json').write_text(json.dumps(plan,indent=2))
print('Prepared exact six-stage ternary and seven-stage hybrid trees')
