from pathlib import Path
import json,shutil,re,math
R=Path('/home/ding/vivado_project/Lab6_growth_trials');S=Path('/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11')
names=['fc1_128x6_dual','zero_gate','tail8','fc1_csa_tree']
def clone(n):
 d=R/n
 if d.exists():raise RuntimeError('Already exists '+str(d))
 for sub in ['rtl','data','tb','tools']:
  shutil.copytree(S/sub,d/sub)
  for f in (d/sub).glob('*'):
   if f.suffix in ['.v','.tcl']:f.write_text(f.read_text().replace(str(S),str(d)))
 (d/'results').mkdir();shutil.copy(S/'timing.xdc',d/'timing.xdc')
 c=json.loads((S/'config.json').read_text());c.update(name=n,source=str(S),options={'growth_trial':n});(d/'config.json').write_text(json.dumps(c,indent=2))
 for f in (d/'tools').glob('run_*.tcl'):
  t=f.read_text().replace('general.maxThreads 8','general.maxThreads 4')
  f.write_text(t)
 (d/'tools/run_sim.tcl').write_text(f'''set_param general.maxThreads 4
create_project validation {d}/simulation -part xc7z020clg400-1 -force
add_files [glob {d}/rtl/*.v]
add_files -fileset sim_1 {d}/tb/tb_quant.v
set_property file_type SystemVerilog [get_files *tb_quant.v]
set_property top tb_quant [get_filesets sim_1]
set_property generic {{CLK_PERIOD=4.09}} [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
close_sim -force
exit
''')
 return d
D={n:clone(n) for n in names}
# 1: three 128-input paired-output cores, 184 DSP in FC1 + 32 FC2 + 4 FC3.
d=D[names[0]];lanes=128;groups=4;pairs=22;lat=15
core=(S/'rtl/fc1_paired.v').read_text().replace('module fc1_paired','module fc1_lane_core').replace('input wire clk_i,rst_n_i,start_i,','input wire clk_i,rst_n_i,start_i,input wire [4095:0] input_vector,')
core=core.replace(' (* rom_style="distributed" *) reg [LANES*8-1:0] inputs[0:GROUPS-1];','').replace('$readmemh(INPUTS,inputs);','').replace('biases[0:63]','biases[0:21]').replace('64*GROUPS','22*GROUPS')
core=core.replace('[15:0] valid_pipe','[14:0] valid_pipe').replace('tag[0:15]','tag[0:14]').replace('b0_pipe[0:15]','b0_pipe[0:14]').replace('b1_pipe[0:15]','b1_pipe[0:14]').replace('tag[15]','tag[14]').replace('valid_pipe[15]','valid_pipe[14]').replace('valid_pipe[14:0]','valid_pipe[13:0]').replace('b0_pipe[15]','b0_pipe[14]').replace('b1_pipe[15]','b1_pipe[14]').replace('j<16','j<15').replace('pair_addr==63','pair_addr==21').replace('input_r<=inputs[issue_group]','input_r<=input_vector[4095-issue_group*LANES*8 -:LANES*8]')
a=core.index(' generate if(LANES/16>0)');b=core.index(' genvar g;generate',a)
core=core[:a]+''' genvar bank;generate for(bank=0;bank<LANES/16;bank=bank+1)begin:weight_bank
 (* rom_style="block" *) reg [399:0] local_weights[0:22*GROUPS-1];
 initial begin
'''+''.join(f'if(bank=={i})$readmemh({{WEIGHTS,"_bank{i}.mem"}},local_weights);\n' for i in range(8))+'''end
 (* dont_touch="yes" *) reg [$clog2(22*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin local_addr<=local_addr+1'b1;
 if(!rst_n_i || (start_i && !running))local_addr<=0;
 weight_r[LANES*25-1-bank*400 -:400]<=local_weights[local_addr];end
 end endgenerate
'''+core[b:];(d/'rtl/fc1_lane_core.v').write_text(core)
raw=[int(v,16) for v in Path('/home/ding/vivado_project/Lab5_optimization/data/stream_pair256_hybrid_weights.mem').read_text().split()]
bias=Path('/home/ding/vivado_project/Lab5_optimization/data/fc1_paired_bias.mem').read_text().split()
def wp(q,k):return (raw[q*2+k//256]>>((255-k%256)*16))&65535 if q<64 else 0
def signed(v,b=8):return v-(1<<b) if v>=(1<<(b-1)) else v
wrapper=['''module fc1_paired #(parameter LANES=256,GROUPS=2,ADDER_LANES=256,DSP_LANES=200,WEIGHTS="",INPUTS="",BIASES="") (
input wire clk_i,rst_n_i,start_i,output wire ready_o,output reg done_o,fc_output_wren_o,
output reg [31:0] fc_output_data_o,fc_output_data_b_o,output reg [6:0] fc_output_addr_o);
reg [2047:0] inputs[0:1];initial $readmemh(INPUTS,inputs);
wire [2:0] v,r;wire [31:0] data[0:2];wire [6:0] addr[0:2];
reg [22:0] slots[0:5];reg [6:0] base;reg [1:0] emit;reg emitting;
assign ready_o=r[0];''']
for pe,ndsp in enumerate([128,56,0]):
 prefix=d/f'data/core{pe}';rows=[]
 for q in range(22):
  for group in range(4):
   row=0
   for l in range(128):
    v=wp(q*3+pe,group*128+l);w0=signed(v&255);w1=signed(v>>8)
    pack=((w1<<16)+w0)&((1<<25)-1) if l<ndsp else v<<9
    row=(row<<25)|pack
   rows.append(f'{row:0800x}')
 for bank in range(8):Path(str(prefix)+f'_bank{bank}.mem').write_text('\n'.join(v[bank*100:(bank+1)*100] for v in rows)+'\n')
 bp=Path(str(prefix)+'_bias.mem');bp.write_text('\n'.join(bias[q*3+pe] if q*3+pe<64 else '0000' for q in range(22))+'\n')
 wrapper.append(f'fc1_lane_core #(.LANES(128),.GROUPS(4),.ADDER_LANES(128),.DSP_LANES({ndsp}),.WEIGHTS("{prefix}"),.BIASES("{bp}")) c{pe}(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.input_vector({{inputs[0],inputs[1]}}),.ready_o(r[{pe}]),.done_o(),.fc_output_wren_o(v[{pe}]),.fc_output_data_o(data[{pe}]),.fc_output_addr_o(addr[{pe}]));')
wrapper.append('''integer j;always @(posedge clk_i)begin
 if(!rst_n_i)begin emitting<=0;emit<=0;done_o<=0;fc_output_wren_o<=0;fc_output_addr_o<=0;fc_output_data_o<=0;fc_output_data_b_o<=0;end
 else begin
  done_o<=0;fc_output_wren_o<=0;
  if(v[0])begin
   for(j=0;j<3;j=j+1)slots[2*j+addr[0][0]]<=data[j][22:0];
   if(addr[0][0])begin base<=addr[0][6:1]*6;emitting<=1;emit<=0;end
  end
  if(emitting)begin
   fc_output_wren_o<=1;fc_output_addr_o<=base+2*emit;
   fc_output_data_o<={9'd0,slots[2*emit]};fc_output_data_b_o<={9'd0,slots[2*emit+1]};
   if(emit==2 || base==126)begin emitting<=0;done_o<=base==126;end
   else emit<=emit+1'b1;
  end
 end
end endmodule''');(d/'rtl/fc1_paired.v').write_text('\n'.join(wrapper))
# Balanced 128-leaf binary tree (7 stages).
s=(S/'rtl/adder_tree.v').read_text();start=['module adder_tree(input wire clk,rst_n,input wire [2047:0] data,output wire [31:0] sum_out);','wire signed [15:0] p[0:127];genvar i;generate for(i=0;i<128;i=i+1)begin assign p[i]=data[2047-i*16 -:16];end endgenerate'];n=128;w=16;prev='p'
for lev in range(7):
 n//=2;start.append(f'reg signed [{w}:0] s{lev}[0:{n-1}];integer j{lev};always @(posedge clk)for(j{lev}=0;j{lev}<{n};j{lev}=j{lev}+1)s{lev}[j{lev}]<={{{prev}[2*j{lev}][{w-1}],{prev}[2*j{lev}]}}+{{{prev}[2*j{lev}+1][{w-1}],{prev}[2*j{lev}+1]}};');prev=f's{lev}';w+=1
start.append('assign sum_out={{9{s6[0][22]}},s6[0]};endmodule');(d/'rtl/adder_tree.v').write_text('\n'.join(start))
# FC2: pair two inputs before the split accumulator. Existing feedback remains interleaved by group index.
f=d/'rtl/fc_stream_pair_output.v';s=f.read_text().replace('input wire [IW-1:0] data_i,','input wire [IW-1:0] data_i,data_b_i,').replace('localparam PW=IW+8;','localparam PW=IW+9;').replace('localparam RW=(NO/2)*25;','localparam RW=NO*25;')
s=s.replace('reg signed [IW-1:0] data_r,data_d;','reg signed [IW-1:0] data_r,data_d,data_b_r,data_b_d;').replace('reg signed [IW-1:0] data_e;','reg signed [IW-1:0] data_e,data_b_e;')
a=s.index('    genvar g;generate');b=s.index('    genvar ch;',a)
s=s[:a]+'''    wire signed [15:0] lane_product[0:NO*2-1];
    genvar g;generate for(g=0;g<NO;g=g+1)begin:packed_mult
      wire signed [24:0] packed_w=weight_e[RW-1-g*25 -:25];
      wire signed [7:0] x=(g<NO/2)?data_e:data_b_e;
      (* use_dsp="yes" *) reg signed [32:0] packed_p;
      always @(posedge clk_i)packed_p<=packed_w*x;
      wire signed [15:0] hi=$signed(packed_p[32:16])+packed_p[15];
      assign lane_product[2*g]=packed_p[15:0];assign lane_product[2*g+1]=hi;
    end
    for(g=0;g<NO;g=g+1)begin:combine
      assign product[g]={lane_product[g][15],lane_product[g]}+{lane_product[g+NO][15],lane_product[g+NO]};
    end endgenerate
'''+s[b:]
s=s.replace('data_r <= data_i;','data_r <= data_i; data_b_r<=data_b_i;').replace('data_d <= data_r;','data_d <= data_r; data_b_d<=data_b_r;').replace('data_e <= data_d;','data_e <= data_d; data_b_e<=data_b_d;');f.write_text(s)
rows=(S/'data/fc2_packed_weights.mem').read_text().split();(d/'data/fc2_packed_weights.mem').write_text('\n'.join(rows[2*i]+rows[2*i+1] for i in range(64))+'\n')
f=d/'rtl/lab5_top.v';s=f.read_text().replace('wire d1,d2;','wire d1,d2;wire [31:0] full1b;wire [7:0] fc1_data_b;').replace('.fc_output_data_o(full1),','.fc_output_data_o(full1),.fc_output_data_b_o(full1b),').replace(' fc_stream_pair_output #',' quantize_signed #(.IW(32),.OW(8),.SHIFT(10),.ROUND(0),.SAT(0)) q1b(.data_i(full1b),.data_o(fc1_data_b));\n fc_stream_pair_output #').replace('.NI(128),.NO(32)', '.NI(64),.NO(32)').replace('.IA(7),.OA(5)','.IA(6),.OA(5)').replace('.data_i(fc1_data_o),.addr_i(fc1_addr_o)', '.data_i(fc1_data_o),.data_b_i(fc1_data_b),.addr_i(fc1_addr_o[6:1])');f.write_text(s)
f=d/'tb/tb_quant.v';s=f.read_text().replace('if(a1!==(n1%128) || e1!==ref1[n1])','if(a1!==(n1%128) || e1!==ref1[n1] || $signed(dut.fc1_data_b)!==ref1[n1+1])').replace('end n1=n1+1;','end n1=n1+2;');f.write_text(s)
# 2: exact zero operand clock-enable/gating; schedule stays unchanged, no promise of lower latency.
d=D['zero_gate'];f=d/'rtl/fc_stream_pair_output.v';s=f.read_text().replace('packed_p<=packed_w*data_e;', 'if(data_e!=0)packed_p<=packed_w*data_e;else packed_p<=0;')
s=s.replace('reg valid_after,last_after,', 'reg [4:0] nonzero_pipe;reg write_after;\n    reg valid_after,last_after,')
s=s.replace('if(valid_pipe[4])begin low', 'if(valid_pipe[4] && (nonzero_pipe[4] || first_pipe[4] || odd_first_pipe[4]))begin low').replace('if(valid_after)begin if(parity_after)', 'if(write_after)begin if(parity_after)')
s=s.replace('valid_pipe<=0; first_pipe<=0;', 'nonzero_pipe<=0;write_after<=0;valid_pipe<=0; first_pipe<=0;').replace('valid_pipe <= {valid_pipe[3:0],valid_i};', 'valid_pipe <= {valid_pipe[3:0],valid_i};\n            nonzero_pipe<={nonzero_pipe[3:0],data_i!=0};write_after<=valid_pipe[4] && (nonzero_pipe[4] || first_pipe[4] || odd_first_pipe[4]);');f.write_text(s)
# 3: FC2 eight-output burst, FC3 eight-input streaming.
d=D['tail8'];f=d/'rtl/fc_stream_pair_output.v';s=f.read_text().replace('data_d_o,','data_d_o,data_e_o,data_f_o,data_g_o,data_h_o,').replace('read_data_c,read_data_d;','read_data_c,read_data_d,read_data_e,read_data_f,read_data_g,read_data_h;')
s=s.replace('read_addr<=emit_idx;', 'read_data_e<=snapshot[emit_idx+4];read_data_f<=snapshot[emit_idx+5];read_data_g<=snapshot[emit_idx+6];read_data_h<=snapshot[emit_idx+7]; read_addr<=emit_idx;').replace('NO-4','NO-8').replace("emit_idx+3'd4","emit_idx+4'd8")
needle='            done_o <= read_valid'
extra=''.join('            data_'+ch+'_o <= (RELU && read_data_'+ch+'[AW-1]) ? {OW{1\'b0}} : {{(OW-AW){read_data_'+ch+'[AW-1]}},read_data_'+ch+'};\n' for ch in 'efgh')
s=s.replace(needle,extra+needle);f.write_text(s)
# Generic eight-input FC3 pipeline: 3 reduction stages + feedback.
f=d/'rtl/fc_stream_two_inputs.v';f.write_text('''module fc_stream_two_inputs #(parameter IW=8,NI=4,NO=2,AW=19,OW=21,IA=2,OA=1,RELU=0,WEIGHT_FILE="",BIAS_FILE="")(
input wire clk_i,rst_n_i,valid_i,input wire [IW-1:0] data_i,data_b_i,data_c_i,data_d_i,data_e_i,data_f_i,data_g_i,data_h_i,
input wire [IA-1:0] addr_i,output reg valid_o,output reg [OW-1:0] data_o,output reg [OA-1:0] addr_o,output reg done_o);
(* rom_style="distributed" *) reg [199:0] weights[0:NI-1];reg signed [7:0] biases[0:1];
initial begin $readmemh(WEIGHT_FILE,weights);$readmemh(BIAS_FILE,biases);end
reg [199:0] weight_r,weight_d;wire [7:0] x[0:7];
assign x[0]=data_i;assign x[1]=data_b_i;assign x[2]=data_c_i;assign x[3]=data_d_i;
assign x[4]=data_e_i;assign x[5]=data_f_i;assign x[6]=data_g_i;assign x[7]=data_h_i;
reg signed [7:0] data_r[0:7],data_d[0:7];wire signed [15:0] prod[0:15];reg signed [15:0] product_r[0:15];
reg signed [16:0] pair_sum[0:7];reg signed [17:0] quad_sum[0:3];reg signed [18:0] sum_r[0:1],acc[0:1];
reg [6:0] valid_pipe,first_pipe,last_pipe;reg emitting,emit_idx,read_valid,read_addr;reg signed [18:0] read_data;
genvar g;generate for(g=0;g<8;g=g+1)begin:mult
 (* use_dsp="yes" *) reg signed [32:0] p;
 wire signed [24:0] w=weight_d[199-g*25 -:25];always @(posedge clk_i)p<=w*data_d[g];
 wire signed [15:0] hi=$signed(p[32:16])+p[15];assign prod[g]=p[15:0];assign prod[8+g]=hi;
end endgenerate
integer j;always @(posedge clk_i)begin
 weight_r<=weights[addr_i];weight_d<=weight_r;
 for(j=0;j<8;j=j+1)begin data_r[j]<=x[j];data_d[j]<=data_r[j];end
 for(j=0;j<16;j=j+1)product_r[j]<=prod[j];
 for(j=0;j<8;j=j+1)pair_sum[j]<={product_r[2*j][15],product_r[2*j]}+{product_r[2*j+1][15],product_r[2*j+1]};
 for(j=0;j<4;j=j+1)quad_sum[j]<={pair_sum[2*j][16],pair_sum[2*j]}+{pair_sum[2*j+1][16],pair_sum[2*j+1]};
 for(j=0;j<2;j=j+1)sum_r[j]<={quad_sum[2*j][17],quad_sum[2*j]}+{quad_sum[2*j+1][17],quad_sum[2*j+1]};
 if(!rst_n_i)begin valid_pipe<=0;first_pipe<=0;last_pipe<=0;emitting<=0;emit_idx<=0;read_valid<=0;valid_o<=0;done_o<=0;addr_o<=0;data_o<=0;end
 else begin
 valid_pipe<={valid_pipe[5:0],valid_i};first_pipe<={first_pipe[5:0],addr_i==0};last_pipe<={last_pipe[5:0],addr_i==NI-1};
 if(valid_pipe[6])begin
 for(j=0;j<2;j=j+1)if(first_pipe[6])acc[j]<=sum_r[j]+{{11{biases[j][7]}},biases[j]};else acc[j]<=acc[j]+sum_r[j];
 if(last_pipe[6])begin emitting<=1;emit_idx<=0;end end
 read_valid<=emitting;if(emitting)begin read_data<=acc[emit_idx];read_addr<=emit_idx;if(emit_idx)emitting<=0;else emit_idx<=1;end
 valid_o<=read_valid;addr_o<=read_addr;data_o<={{2{read_data[18]}},read_data};done_o<=read_valid && read_addr;
 end
end endmodule
''')
rows=(S/'data/fc3_packed_weights.mem').read_text().split();(d/'data/fc3_packed_weights.mem').write_text('\n'.join(rows[2*i]+rows[2*i+1] for i in range(4))+'\n')
f=d/'rtl/lab5_top.v';s=f.read_text().replace(' wire d1,d2;', ' wire [22:0] full2e,full2f,full2g,full2h;wire [7:0] d2e,d2f,d2g,d2h;\n wire d1,d2;').replace('.data_d_o(full2d),', '.data_d_o(full2d),.data_e_o(full2e),.data_f_o(full2f),.data_g_o(full2g),.data_h_o(full2h),')
s=s.replace(' fc_stream_two_inputs #', ''.join(f' quantize_signed #(.IW(23),.OW(8),.SHIFT(9),.ROUND(0),.SAT(0)) q2{ch}(.data_i(full2{ch}),.data_o(d2{ch}));\n' for ch in 'efgh')+' fc_stream_two_inputs #').replace('.NI(8),.NO(2)', '.NI(4),.NO(2)').replace('.IA(3),.OA(1)', '.IA(2),.OA(1)').replace('.addr_i(fc2_addr_o[4:2])', '.data_e_i(d2e),.data_f_i(d2f),.data_g_i(d2g),.data_h_i(d2h),.addr_i(fc2_addr_o[4:3])');f.write_text(s)
f=d/'tb/tb_quant.v';s=f.read_text().replace('e2d!==ref2[n2+3]', 'e2d!==ref2[n2+3]'+''.join(f' || $signed(dut.d2{ch})!==ref2[n2+{k}]' for ch,k in zip('efgh',range(4,8)))).replace('end n2=n2+4;', 'end n2=n2+8;');f.write_text(s)
# 4: one carry-save compression stage followed by an eight-stage binary tree.
d=D['fc1_csa_tree'];lines=['module adder_tree(input wire clk,rst_n,input wire [4095:0] data,output wire [31:0] sum_out);','wire signed [15:0] p[0:255];genvar i;generate for(i=0;i<256;i=i+1)begin assign p[i]=data[4095-i*16 -:16];end endgenerate','reg signed [17:0] csa[0:171];']
for g in range(86):
 terms=[f'{{{{2{{p[{g*3+k}][15]}}}},p[{g*3+k}]}}' if g*3+k<256 else "18'd0" for k in range(3)]
 a,b,c=terms;lines.append(f'always @(posedge clk)begin csa[{2*g}]<={a}^{b}^{c};csa[{2*g+1}]<=(({a}&{b})|({a}&{c})|({b}&{c}))<<1;end')
n=172;w=18;prev='csa';proof=[]
for lev in range(8):
 nxt=(n+1)//2;lines.append(f'reg signed [{w}:0] s{lev}[0:{nxt-1}];')
 for j in range(nxt):
  a=f'{{{prev}[{2*j}][{w-1}],{prev}[{2*j}]}}';b=f'{{{prev}[{2*j+1}][{w-1}],{prev}[{2*j+1}]}}' if 2*j+1<n else f"{w+1}'d0"
  lines.append(f'always @(posedge clk)s{lev}[{j}]<={a}+{b};')
 n=nxt;w+=1;prev=f's{lev}'
assert n==1;lines.append('assign sum_out={{6{s7[0][25]}},s7[0]};endmodule');(d/'rtl/adder_tree.v').write_text('\n'.join(lines))
f=d/'rtl/fc1_paired.v';s=f.read_text().replace('[15:0] valid_pipe','[16:0] valid_pipe').replace('tag[0:15]','tag[0:16]').replace('b0_pipe[0:15]','b0_pipe[0:16]').replace('b1_pipe[0:15]','b1_pipe[0:16]').replace('tag[15]','tag[16]').replace('valid_pipe[15]','valid_pipe[16]').replace('valid_pipe[14:0]','valid_pipe[15:0]').replace('b0_pipe[15]','b0_pipe[16]').replace('b1_pipe[15]','b1_pipe[16]').replace('j<16','j<17');f.write_text(s)
(R/'results/plan.json').write_text(json.dumps({'baseline':str(S),'baseline_ns':711.66,'candidates':names,'budget':{'dsp_max':220,'lut_max':53200,'ff_max':106400,'bram_max':140,'carry4_max':13300,'max_threads_each':4,'full_implementations_per_candidate':1},'notes':'Only exact INT8 candidates; zeros gating preserves schedule; no model change or new multipump attempt.'},indent=2))
print('Prepared',names)

import runpy
runpy.run_path(str(R/"tools/fix_tail_budget.py"))
