from pathlib import Path
import shutil,json,re
ROOT=Path('/home/ding/vivado_project/Lab6_architecture_trials')
SRC=Path('/home/ding/vivado_project/Lab6_limit_search/quick_fc2_rom_pipe')

def clone(name):
 d=ROOT/name
 if d.exists():raise RuntimeError(f'Existing trial {d}')
 d.mkdir();(d/'results').mkdir()
 for sub in ['rtl','data','tb','tools']:
  shutil.copytree(SRC/sub,d/sub)
  for p in (d/sub).glob('*'):
   if p.suffix in ['.v','.tcl']:p.write_text(p.read_text().replace(str(SRC),str(d)).replace(SRC.name,name))
 shutil.copy2(SRC/'timing.xdc',d/'timing.xdc')
 p=d/'tools/run_synth.tcl';p.write_text(p.read_text().replace('general.maxThreads 8','general.maxThreads 4'))
 cfg=json.loads((SRC/'config.json').read_text());cfg.update(name=name,source=str(SRC));cfg['options']={'architecture_trial':name}
 (d/'config.json').write_text(json.dumps(cfg,indent=2))
 return d

raw=[int(s,16) for s in Path('/home/ding/vivado_project/Lab5_optimization/data/stream_pair256_hybrid_weights.mem').read_text().split()]
bias=Path('/home/ding/vivado_project/Lab5_optimization/data/fc1_paired_bias.mem').read_text().split()
def weight(pair,k):return (raw[pair*2+k//256]>>((255-k%256)*16))&65535
def tree(lanes):
 n=lanes;w=16;parts=[f'module adder_tree(input wire clk,rst_n,input wire [{lanes*16-1}:0] data,output wire [31:0] sum_out);',f'wire signed [15:0] p[0:{lanes-1}];genvar i;generate for(i=0;i<{lanes};i=i+1)begin:cut assign p[i]=data[{lanes*16-1}-i*16 -:16];end endgenerate']
 prev='p'
 for stage in range(lanes.bit_length()-1):
  n//=2
  parts.append(f'reg signed [{w}:0] s{stage}[0:{n-1}];integer j{stage};always @(posedge clk)for(j{stage}=0;j{stage}<{n};j{stage}=j{stage}+1)s{stage}[j{stage}]<={{ {prev}[2*j{stage}][{w-1}],{prev}[2*j{stage}] }}+{{ {prev}[2*j{stage}+1][{w-1}],{prev}[2*j{stage}+1] }};')
  prev=f's{stage}';w+=1
 parts.append(f'assign sum_out={{{{{32-w}{{{prev}[0][{w-1}]}}}},{prev}[0]}};endmodule')
 return '\n'.join(parts)+'\n'

for lanes in [128,64]:
 pe=256//lanes;groups=512//lanes;pairs=64//pe;gw=groups.bit_length()-1;lat=16-(8-(lanes.bit_length()-1))
 d=clone(f'fc1_simd{lanes}_pe{pe*2}')
 core=(SRC/'rtl/fc1_paired.v').read_text()
 core=core.replace('module fc1_paired','module fc1_lane_core').replace('input wire clk_i,rst_n_i,start_i,','input wire clk_i,rst_n_i,start_i,input wire [4095:0] input_vector,')
 core=core.replace(' (* rom_style="distributed" *) reg [LANES*8-1:0] inputs[0:GROUPS-1];','').replace('$readmemh(INPUTS,inputs);','')
 core=core.replace('biases[0:63]',f'biases[0:{pairs-1}]').replace('64*GROUPS',f'{pairs}*GROUPS')
 core=core.replace('reg [1:0] issue_group;',f'reg [{gw-1}:0] issue_group;')
 core=core.replace('reg [15:0] valid_pipe;reg [7:0] tag[0:15];',f'reg [{lat-1}:0] valid_pipe;reg [{6+gw-1}:0] tag[0:{lat-1}];')
 core=core.replace('tag[15]',f'tag[{lat-1}]').replace('valid_pipe[15]',f'valid_pipe[{lat-1}]').replace('valid_pipe[14:0]',f'valid_pipe[{lat-2}:0]').replace('j<16',f'j<{lat}')
 core=core.replace('[7:2]',f'[{gw+5}:{gw}]').replace('[1:0]==',f'[{gw-1}:0]==').replace('pair_addr==63',f'pair_addr=={pairs-1}')
 core=core.replace('input_r<=inputs[issue_group]', 'input_r<=input_vector[4095-issue_group*LANES*8 -:LANES*8]')
 a=core.index(' generate if(LANES/16>0)');z=core.index(' genvar g;generate',a)
 core=core[:a]+f''' genvar bank;generate for(bank=0;bank<LANES/16;bank=bank+1)begin:weight_bank
 (* rom_style="block" *) reg [399:0] local_weights[0:{pairs}*GROUPS-1];
 initial $readmemh($sformatf("%s_bank%0d.mem",WEIGHTS,bank),local_weights);
 (* dont_touch="yes" *) reg [$clog2({pairs}*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin
 local_addr<=local_addr+1'b1;if(!rst_n_i || (start_i && !running))local_addr<=0;
 weight_r[LANES*25-1-bank*400 -:400]<=local_weights[local_addr];end
 end endgenerate
'''+core[z:]
 core=core.replace('initial $readmemh($sformatf("%s_bank%0d.mem",WEIGHTS,bank),local_weights);','initial begin\n'+''.join(f'if(bank=={b})$readmemh({{WEIGHTS,"_bank{b}.mem"}},local_weights);\n' for b in range(lanes//16))+'end')
 (d/'rtl/fc1_lane_core.v').write_text(core)
 (d/'rtl/adder_tree.v').write_text(tree(lanes))
 wrapper=['module fc1_paired #(parameter LANES=256,GROUPS=2,ADDER_LANES=256,DSP_LANES=200,WEIGHTS="",INPUTS="",BIASES="") (input wire clk_i,rst_n_i,start_i,output wire ready_o,output reg done_o,output reg fc_output_wren_o,output reg [31:0] fc_output_data_o,output reg [6:0] fc_output_addr_o);','(* rom_style="distributed" *) reg [2047:0] inputs[0:1];initial $readmemh(INPUTS,inputs);',f'wire [{pe-1}:0] v,r;wire [31:0] data[0:{pe-1}];wire [6:0] addr[0:{pe-1}];', 'reg [22:0] queue[0:127];reg [127:0] available;reg [6:0] emit_idx;integer j;assign ready_o=r[0];']
 for p in range(pe):
  ndsp=max(0,min(lanes,200-p*lanes));prefix=d/f'data/core{p}'
  rows=[]
  for q in range(pairs):
   for group in range(groups):
    row=0
    for l in range(lanes):
     v=weight(q*pe+p,group*lanes+l);w0=v&255;w1=v>>8
     w0=w0-256 if w0>=128 else w0;w1=w1-256 if w1>=128 else w1
     packed=(((w1<<16)+w0)&((1<<25)-1)) if l<ndsp else v<<9
     row=(row<<25)|packed
    rows.append(f'{row:0{lanes*25//4}x}')
  for bank in range(lanes//16):Path(f'{prefix}_bank{bank}.mem').write_text('\n'.join(r[bank*100:(bank+1)*100] for r in rows)+'\n')
  bp=d/f'data/core{p}_bias.mem';bp.write_text('\n'.join(bias[q*pe+p] for q in range(pairs))+'\n')
  wrapper.append(f'fc1_lane_core #(.LANES({lanes}),.GROUPS({groups}),.ADDER_LANES({lanes}),.DSP_LANES({ndsp}),.WEIGHTS("{prefix}"),.BIASES("{bp}")) c{p}(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.input_vector({{inputs[0],inputs[1]}}),.ready_o(r[{p}]),.done_o(),.fc_output_wren_o(v[{p}]),.fc_output_data_o(data[{p}]),.fc_output_addr_o(addr[{p}]));')
 wrapper.append('always @(posedge clk_i)begin if(!rst_n_i)begin available<=0;emit_idx<=0;done_o<=0;fc_output_wren_o<=0;fc_output_data_o<=0;fc_output_addr_o<=0;end else begin done_o<=0;fc_output_wren_o<=0;')
 for p in range(pe):
  idx=f'(addr[{p}][6:1]*{2*pe}+{2*p}+addr[{p}][0])'
  wrapper.append(f'if(v[{p}])begin queue[{idx}]<=data[{p}][22:0];available[{idx}]<=1;end')
 wrapper.append("if(available[emit_idx])begin fc_output_wren_o<=1;fc_output_addr_o<=emit_idx;fc_output_data_o<={9'd0,queue[emit_idx]};available[emit_idx]<=0;if(emit_idx==127)begin emit_idx<=0;done_o<=1;end else emit_idx<=emit_idx+1'b1;end end end endmodule")
 (d/'rtl/fc1_paired.v').write_text('\n'.join(wrapper)+'\n')

# Two-way interleaved accumulators; split each carry chain across two clocks.
d=clone('fc2_interleaved_split11')
p=d/'rtl/fc_stream_pair_output.v';s=p.read_text()
s=s.replace('reg [4:0] valid_pipe, first_pipe, last_pipe;', 'reg [4:0] valid_pipe, first_pipe, last_pipe,odd_first_pipe,parity_pipe;\n    reg valid_after,last_after,parity_after,merge_pending,snapshot_pending;')
a=s.index('    integer j;')
s=s[:a]+'''    genvar ch;generate for(ch=0;ch<NO;ch=ch+1)begin:interleaved
      reg signed [AW-1:0] even_acc,odd_acc;
      wire signed [AW-1:0] prod={{(AW-PW){product_r[ch][PW-1]}},product_r[ch]};
      wire signed [AW-1:0] bias={{(AW-8){biases[ch][7]}},biases[ch]};
      wire [AW-1:0] base=first_pipe[4]?bias:(odd_first_pipe[4]?{AW{1'b0}}:(parity_pipe[4]?odd_acc:even_acc));
      reg [11:0] low;reg [AW-12:0] upper_a,upper_b;
      wire [AW-12:0] upper_sum=upper_a+upper_b+low[11];
      reg [11:0] merge_low;reg [AW-12:0] merge_a,merge_b;
      wire [AW-12:0] merge_hi=merge_a+merge_b+merge_low[11];
      always @(posedge clk_i)begin
        if(valid_pipe[4])begin low<={1'b0,base[10:0]}+{1'b0,prod[10:0]};upper_a<=base[AW-1:11];upper_b<=prod[AW-1:11];end
        if(valid_after)begin if(parity_after)odd_acc<={upper_sum,low[10:0]};else even_acc<={upper_sum,low[10:0]};end
        if(merge_pending)begin merge_low<={1'b0,even_acc[10:0]}+{1'b0,odd_acc[10:0]};merge_a<=even_acc[AW-1:11];merge_b<=odd_acc[AW-1:11];end
        if(snapshot_pending)snapshot[ch]<={merge_hi,merge_low[10:0]};
      end
    end endgenerate
'''+s[a:]
s=s.replace('valid_pipe<=0; first_pipe<=0; last_pipe<=0;', 'valid_pipe<=0; first_pipe<=0; last_pipe<=0;odd_first_pipe<=0;parity_pipe<=0;valid_after<=0;last_after<=0;parity_after<=0;merge_pending<=0;snapshot_pending<=0;')
needle='last_pipe <= {last_pipe[3:0],addr_i==NI-1};'
s=s.replace(needle,needle+'''\n            odd_first_pipe<={odd_first_pipe[3:0],addr_i==1};parity_pipe<={parity_pipe[3:0],addr_i[0]};
            valid_after<=valid_pipe[4];last_after<=last_pipe[4];parity_after<=parity_pipe[4];
            merge_pending<=valid_after && last_after;snapshot_pending<=merge_pending;''')
a=s.index('            if(valid_pipe[4]) begin');z=s.index('            read_valid<=emitting;',a)
s=s[:a]+"            if(snapshot_pending)begin emitting<=1;emit_idx<=0;end\n"+s[z:];p.write_text(s)

# Reuse the proven runner without modifying the older project or plan.
(ROOT/'tools/run.py').write_text("import sys\nfrom pathlib import Path\nsys.path.insert(0,'/home/ding/vivado_project/Lab6_bottleneck_optimization/tools')\nimport run as runner\nrunner.ROOT=Path('/home/ding/vivado_project/Lab6_architecture_trials')\nfor arg in sys.argv[1:]:\n name,stage=arg.split(':')\n if not runner.run(name,stage):raise SystemExit(1)\n")
(ROOT/'results/plan.json').write_text(json.dumps({'baseline':str(SRC),'baseline_latency_ns':735.3,'candidates':['fc1_simd128_pe4','fc1_simd64_pe8','fc2_interleaved_split11'],'budget':{'dsp':220,'bram_expected':68,'rom_weight_bandwidth_bits_per_cycle':6400,'fc1_compute_issue_cycles':128,'fc1_queue_bits_max':2944,'fc2_extra_accumulator_bits':672},'stop':'One routed implementation per numerical-valid and resource-feasible candidate; no iterative ps tuning.'},indent=2))
print('Prepared two FC1 mappings and one split/interleaved FC2 candidate')
