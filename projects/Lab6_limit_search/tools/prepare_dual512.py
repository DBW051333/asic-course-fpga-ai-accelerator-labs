from pathlib import Path
import json,shutil
R=Path('/home/ding/vivado_project/Lab6_limit_search');src=R/'prepack_banked_lookup';d=R/'dual512_lookup';D=Path('/home/ding/vivado_project/Lab5_optimization/data')
for sub in ['rtl','data','tb','tools']:
 shutil.copytree(src/sub,d/sub,dirs_exist_ok=True)
 for p in (d/sub).glob('*'):
  if p.suffix in ['.v','.tcl']:p.write_text(p.read_text().replace(str(src),str(d)).replace(src.name,d.name))
(d/'results').mkdir(exist_ok=True);shutil.copy2(src/'timing.xdc',d/'timing.xdc')
# Fold the two 256-feature groups into one 512-feature group.
raw=[int(v,16) for v in (D/'stream_pair256_hybrid_weights.mem').read_text().split()];packed=[]
for pair in range(64):
 row=(raw[2*pair]<<4096)|raw[2*pair+1];out=0
 for g in range(512):
  v=(row>>((511-g)*16))&65535;w0=v&255;w1=v>>8
  w0=w0-256 if w0>=128 else w0;w1=w1-256 if w1>=128 else w1
  v=(((w1<<16)+w0)&((1<<25)-1)) if g<184 else v<<9
  out=(out<<25)|v
 packed.append(f'{out:03200x}')
(d/'data/fc1_prepacked.mem').write_text('\n'.join(packed)+'\n')
for b in range(32):(d/f'data/fc1_bank{b}.mem').write_text('\n'.join(r[b*100:(b+1)*100] for r in packed)+'\n')
(d/'data/fc1_inputs.mem').write_text(''.join((D/'stream_pair256_hybrid_inputs.mem').read_text().split())+'\n')
rows=(src/'data/fc2_packed_weights.mem').read_text().split();(d/'data/fc2_packed_weights.mem').write_text('\n'.join(rows[i]+rows[i+1] for i in range(0,128,2))+'\n')
# Add the ninth binary sum stage with full signed range.
s=['module adder_tree(input wire clk,rst_n,input wire [8191:0] data,output wire [31:0] sum_out);','wire signed [15:0] p[0:511];genvar i;generate for(i=0;i<512;i=i+1)begin assign p[i]=data[8191-i*16 -:16];end endgenerate']
for level in range(9):
 n=512>>(level+1);w=17+level;prev='p' if level==0 else f's{level-1}'
 s += [f'reg signed [{w-1}:0] s{level}[0:{n-1}];integer j{level};',f'always @(posedge clk)for(j{level}=0;j{level}<{n};j{level}=j{level}+1)s{level}[j{level}]<=$signed({{{prev}[2*j{level}][{w-2}],{prev}[2*j{level}]}})+$signed({{{prev}[2*j{level}+1][{w-2}],{prev}[2*j{level}+1]}});']
s+=['assign sum_out={{7{s8[0][24]}},s8[0]};endmodule'];(d/'rtl/adder_tree.v').write_text('\n'.join(s)+'\n')
p=d/'rtl/fc1_paired.v';s=p.read_text().replace('fc_output_data_o,','fc_output_data_o,fc_output_data_b_o,')
a=s.index(' generate if(LANES/16>0)');z=s.index(' genvar g;generate',a);blocks=[]
for b in range(32):
 blocks.append(f''' generate if(LANES/16>{b})begin:address_bank{b}
 (* rom_style="block" *) reg [399:0] local_weights[0:64*GROUPS-1];
 initial $readmemh("{d}/data/fc1_bank{b}.mem",local_weights);
 (* dont_touch="yes" *) reg [$clog2(64*GROUPS)-1:0] local_addr;
 always @(posedge clk_i)begin local_addr<=local_addr+1'b1;
 if(!rst_n_i || (start_i && !running))local_addr<=0;
 weight_r[LANES*25-1-{b}*400 -:400]<=local_weights[local_addr];end
 end endgenerate\n''')
s=s[:a]+''.join(blocks)+s[z:]
s=s.replace('[15:0] valid_pipe','[16:0] valid_pipe').replace('tag[0:15]','tag[0:16]').replace('tag[15]','tag[16]').replace('valid_pipe[15]','valid_pipe[16]').replace('valid_pipe[14:0]','valid_pipe[15:0]').replace('j<16','j<17')
a=s.index('   if(emitting==1)begin');z=s.index('   if(valid_pipe[16])',a)
s=s[:a]+'''   if(emitting==1)begin
    fc_output_wren_o<=1;fc_output_addr_o<={pair_addr,1'b0};
    fc_output_data_o<=pair0[22]?32'd0:{{9{pair0[22]}},pair0};
    fc_output_data_b_o<=pair1[22]?32'd0:{{9{pair1[22]}},pair1};
    done_o<=pair_addr==63;emitting<=0;
   end
'''+s[z:]
s=s.replace('pair0<=acc0+group_sum0;pair1<=acc1+group_sum1;', 'pair0<=group_sum0+b0;pair1<=group_sum1+b1;');p.write_text(s)
# Two activation streams, 32 packed DSP multipliers and an extra exact sum stage.
p=d/'rtl/fc_stream_pair_output.v';s=p.read_text().replace('data_i,','data_i,data_b_i,').replace('localparam RW=(NO/2)*25','localparam RW=NO*25').replace('data_r,data_d;','data_r,data_d,data_b_r,data_b_d;').replace('product [0:NO-1]','product [0:NO*2-1]').replace('product_r [0:NO-1]','product_r [0:NO*2-1]')
s=s.replace('reg [3:0] valid_pipe', 'reg signed [PW:0] sum_r [0:NO-1];\n    reg [4:0] valid_pipe').replace('g<NO/2','g<NO')
s=s.replace('packed_p<=packed_w*data_d;', "packed_p<=packed_w*((g<NO/2)?data_d:data_b_d);")
s=s.replace('data_r <= data_i;', 'data_r <= data_i;data_b_r<=data_b_i;').replace('data_d <= data_r;', 'data_d <= data_r;data_b_d<=data_b_r;')
s=s.replace('for(j=0;j<NO;j=j+1) begin\n            product_r', 'for(j=0;j<NO*2;j=j+1) begin\n            product_r')
s=s.replace('        if(!rst_n_i) begin', '        for(j=0;j<NO;j=j+1)sum_r[j]<=$signed({product_r[j][PW-1],product_r[j]})+$signed({product_r[j+NO][PW-1],product_r[j+NO]});\n        if(!rst_n_i) begin')
s=s.replace('[2:0],','[3:0],').replace('valid_pipe[3]','valid_pipe[4]').replace('first_pipe[3]','first_pipe[4]').replace('last_pipe[3]','last_pipe[4]')
s=s.replace('{{(AW-PW){product_r[j][PW-1]}},product_r[j]}','{{(AW-PW-1){sum_r[j][PW]}},sum_r[j]}');p.write_text(s)
p=d/'rtl/lab5_top.v';s=p.read_text().replace('fc1_data_o,','fc1_data_o,fc1_data_b_o,').replace('full1;','full1,full1b;').replace('.LANES(256),.GROUPS(2),.ADDER_LANES(256),.DSP_LANES(200)', '.LANES(512),.GROUPS(1),.ADDER_LANES(512),.DSP_LANES(184)').replace(str(D/'stream_pair256_hybrid_inputs.mem'),str(d/'data/fc1_inputs.mem')).replace('.fc_output_data_o(full1),','.fc_output_data_o(full1),.fc_output_data_b_o(full1b),').replace(' fc_stream_pair_output #', ' quantize_signed #(.IW(32),.OW(8),.SHIFT(10),.ROUND(0),.SAT(0)) q1b(.data_i(full1b),.data_o(fc1_data_b_o));\n fc_stream_pair_output #').replace('.NI(128),.NO(32)','.NI(64),.NO(32)').replace('.IA(7),.OA(5)', '.IA(6),.OA(5)').replace('.data_i(fc1_data_o),.addr_i(fc1_addr_o)', '.data_i(fc1_data_o),.data_b_i(fc1_data_b_o),.addr_i(fc1_addr_o[6:1])');p.write_text(s)
p=d/'tb/tb_quant.v';s=p.read_text().replace('wire [7:0] d1;', 'wire [7:0] d1,d1b;').replace('e1=$signed(d1),', 'e1=$signed(d1),e1b=$signed(d1b),').replace('.fc1_data_o(d1),', '.fc1_data_o(d1),.fc1_data_b_o(d1b),')
s=s.replace('for(gg=0;gg<2;gg=gg+1)for(ll=0;ll<256;ll=ll+1) dut.u_fc1.inputs[gg][2047-ll*8 -:8]=input_bytes[job*512+gg*256+ll];','for(ll=0;ll<512;ll=ll+1) dut.u_fc1.inputs[0][4095-ll*8 -:8]=input_bytes[job*512+ll];')
s=s.replace('e1!==ref1[n1]', 'e1!==ref1[n1] || e1b!==ref1[n1+1]').replace('end n1=n1+1;', 'end n1=n1+2;');p.write_text(s)
c=json.loads((src/'config.json').read_text());c.update(name=d.name,source=str(src),tree_stages=9,cycles=0,interval_cycles=65,dsp1=184);c['options'].update(lanes=512,groups=1,fc1_outputs_per_cycle=2,fc2_inputs_per_cycle=2);(d/'config.json').write_text(json.dumps(c,indent=2));p=R/'results/plan.json';c=json.loads(p.read_text());c['candidates'].append(d.name);p.write_text(json.dumps(c,indent=2))
print('Prepared 512-lane FC1 with two outputs and two-input FC2; DSP budget 184+32+4=220')
