from pathlib import Path
import shutil
r=Path('/home/ding/vivado_project/Lab5_optimization');src=r/'stream_pair256_partial5_clk5';d=r/'stream_pair256_dualtail_clk5'
for n in ['rtl','tb','tools']:shutil.copytree(src/n,d/n,dirs_exist_ok=True)
(d/'results').mkdir(exist_ok=True)
s=(d/'rtl/fc_stream.v').read_text().replace('module fc_stream #','module fc_stream_pair_output #')
s=s.replace('output reg [OW-1:0] data_o,','output reg [OW-1:0] data_o, data_b_o,').replace('reg signed [AW-1:0] read_data;','reg signed [AW-1:0] read_data, read_data_b;')
s=s.replace('read_data<=acc[emit_idx];','read_data<=acc[emit_idx]; read_data_b<=acc[emit_idx+1\'b1];').replace('emit_idx==NO-1','emit_idx==NO-2').replace("emit_idx+1'b1","emit_idx+2'd2")
# restore neighboring accumulator address to +1, not stride +2
s=s.replace("read_data_b<=acc[emit_idx+2'd2]","read_data_b<=acc[emit_idx+1'b1]")
s=s.replace('done_o <= read_valid && (read_addr==NO-1);', '''data_b_o <= (RELU && read_data_b[AW-1]) ? {OW{1'b0}} : {{(OW-AW){read_data_b[AW-1]}},read_data_b};
            done_o <= read_valid && (read_addr==NO-2);''')
(d/'rtl/fc_stream_pair_output.v').write_text(s)
s=(d/'rtl/fc_stream.v').read_text().replace('module fc_stream #','module fc_stream_two_inputs #').replace('input wire [IW-1:0] data_i,','input wire [IW-1:0] data_i, data_b_i,')
s=s.replace('NO*8','NO*16').replace('reg signed [IW-1:0] data_r,data_d;','reg signed [IW-1:0] data_r,data_d,data_b_r,data_b_d;')
s=s.replace('data_r <= data_i;','data_r <= data_i; data_b_r<=data_b_i;').replace('data_d <= data_r;','data_d <= data_r; data_b_d<=data_b_r;')
s=s.replace('product [0:NO-1]','product [0:NO*2-1]').replace('product_r [0:NO-1]','product_r [0:NO*2-1];\n    reg signed [PW:0] sum_r [0:NO-1]')
s=s.replace('product[j] <= data_d * $signed(weight_d[NO*16-1-j*8 -:8]);\n            product_r[j] <= product[j];','''product[j*2] <= data_d * $signed(weight_d[NO*16-1-j*16 -:8]);
            product[j*2+1] <= data_b_d * $signed(weight_d[NO*16-9-j*16 -:8]);
            product_r[j*2] <= product[j*2]; product_r[j*2+1]<=product[j*2+1];
            sum_r[j] <= {product_r[j*2][PW-1],product_r[j*2]}+{product_r[j*2+1][PW-1],product_r[j*2+1]};''')
s=s.replace('[3:0] valid_pipe','[4:0] valid_pipe').replace('[2:0]','[3:0]').replace('pipe[3]','pipe[4]').replace('{{(AW-PW){product_r[j][PW-1]}},product_r[j]}','{{(AW-PW-1){sum_r[j][PW]}},sum_r[j]}')
(d/'rtl/fc_stream_two_inputs.v').write_text(s)
a=[int(x,16) for x in (r/'data/fc3_weights.mem').read_text().split()];lines=[]
for i in range(16):
 w0a=(a[i*2]>>8)&255;w1a=a[i*2]&255;w0b=(a[i*2+1]>>8)&255;w1b=a[i*2+1]&255
 lines.append(f'{w0a:02x}{w0b:02x}{w1a:02x}{w1b:02x}')
(r/'data/fc3_dual_weights.mem').write_text('\n'.join(lines)+'\n')
p=d/'rtl/lab5_top.v';s=p.read_text().replace('output wire [47:0] fc2_data_o,','output wire [47:0] fc2_data_o, fc2_data_b_o,')
s=s.replace('fc_stream #(.IW(23)','fc_stream_pair_output #(.IW(23)').replace('.data_o(fc2_data_o),','.data_o(fc2_data_o),.data_b_o(fc2_data_b_o),')
s=s.replace('fc_stream #(.IW(35),.NI(32)','fc_stream_two_inputs #(.IW(35),.NI(16)').replace('.IA(5),.OA(1)','.IA(4),.OA(1)').replace('data/fc3_weights.mem','data/fc3_dual_weights.mem').replace('.data_i(fc2_data_o[34:0]),.addr_i(fc2_addr_o)','.data_i(fc2_data_o[34:0]),.data_b_i(fc2_data_b_o[34:0]),.addr_i(fc2_addr_o[4:1])');p.write_text(s)
for p in [d/'tb/tb_lab5_top.v',d/'tb/tb_lab5_validation.v']:
 s=p.read_text().replace('wire [47:0] d2;','wire [47:0] d2,d2b;').replace('.fc2_data_o(d2),','.fc2_data_o(d2),.fc2_data_b_o(d2b),')
 s=s.replace('n2=n2+1;', '''n2=n2+1;
  if({{16{d2b[47]}},d2b}!==ref2[n2])begin errors=errors+1;$display("MISMATCH FC2[%0d] %d",n2,$signed(d2b));end
  n2=n2+1;''');p.write_text(s)
for p in (d/'tools').glob('*.tcl'):
 s=p.read_text().replace(str(src),str(d)).replace('stream_pair256_partial5_clk5.xpr',d.name+'.xpr').replace('create_project stream_pair256_partial5_clk5','create_project '+d.name);p.write_text(s)
print(d)
