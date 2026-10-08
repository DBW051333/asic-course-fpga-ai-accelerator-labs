from pathlib import Path
import shutil
r=Path('/home/ding/vivado_project/Lab5_optimization');src=r/'stream_pair256_dualtail_clk5';d=r/'stream_pair256_quadtail_clk5'
for n in ['rtl','tb','tools']:shutil.copytree(src/n,d/n,dirs_exist_ok=True)
(d/'results').mkdir(exist_ok=True)
p=d/'rtl/fc_stream_pair_output.v';s=p.read_text().replace('data_o, data_b_o,','data_o, data_b_o, data_c_o, data_d_o,').replace('read_data, read_data_b;','read_data, read_data_b,read_data_c,read_data_d;')
s=s.replace("read_data_b<=acc[emit_idx+1'b1];","read_data_b<=acc[emit_idx+1'b1];read_data_c<=acc[emit_idx+2'd2];read_data_d<=acc[emit_idx+2'd3];")
s=s.replace('NO-2','NO-4').replace("emit_idx+2'd2;","emit_idx+3'd4;")
s=s.replace('            done_o <=', '''            data_c_o <= (RELU && read_data_c[AW-1]) ? {OW{1'b0}} : {{(OW-AW){read_data_c[AW-1]}},read_data_c};
            data_d_o <= (RELU && read_data_d[AW-1]) ? {OW{1'b0}} : {{(OW-AW){read_data_d[AW-1]}},read_data_d};
            done_o <=''');p.write_text(s)
p=d/'rtl/fc_stream_two_inputs.v';s=p.read_text().replace('data_i, data_b_i,','data_i, data_b_i, data_c_i, data_d_i,').replace('NO*16','NO*32').replace('NO*2','NO*4')
s=s.replace('data_r,data_d,data_b_r,data_b_d;','data_r,data_d,data_b_r,data_b_d,data_c_r,data_c_d,data_d_r,data_d_d;')
s=s.replace('reg signed [PW:0] sum_r [0:NO-1];','reg signed [PW:0] sum_a [0:NO-1],sum_b [0:NO-1];\n    reg signed [PW+1:0] sum_r [0:NO-1];')
s=s.replace('data_b_r<=data_b_i;','data_b_r<=data_b_i;data_c_r<=data_c_i;data_d_r<=data_d_i;').replace('data_b_d<=data_b_r;','data_b_d<=data_b_r;data_c_d<=data_c_r;data_d_d<=data_d_r;')
a=s.index('            product[j*2]');b=s.index('\n        end',a)
s=s[:a]+'''            product[j*4] <= data_d * $signed(weight_d[NO*32-1-j*32 -:8]);
            product[j*4+1] <= data_b_d * $signed(weight_d[NO*32-9-j*32 -:8]);
            product[j*4+2] <= data_c_d * $signed(weight_d[NO*32-17-j*32 -:8]);
            product[j*4+3] <= data_d_d * $signed(weight_d[NO*32-25-j*32 -:8]);
            product_r[j*4]<=product[j*4];product_r[j*4+1]<=product[j*4+1];
            product_r[j*4+2]<=product[j*4+2];product_r[j*4+3]<=product[j*4+3];
            sum_a[j]<={product_r[j*4][PW-1],product_r[j*4]}+{product_r[j*4+1][PW-1],product_r[j*4+1]};
            sum_b[j]<={product_r[j*4+2][PW-1],product_r[j*4+2]}+{product_r[j*4+3][PW-1],product_r[j*4+3]};
            sum_r[j]<={sum_a[j][PW],sum_a[j]}+{sum_b[j][PW],sum_b[j]};'''+s[b:]
s=s.replace('[4:0] valid_pipe','[5:0] valid_pipe').replace('[3:0]','[4:0]').replace('pipe[4]','pipe[5]').replace('{{(AW-PW-1){sum_r[j][PW]}},sum_r[j]}','{{(AW-PW-2){sum_r[j][PW+1]}},sum_r[j]}');p.write_text(s)
a=[int(x,16) for x in (r/'data/fc3_weights.mem').read_text().split()];lines=[]
for i in range(8):
 vals=[]
 for j in range(2):
  for k in range(4):vals.append((a[i*4+k]>>(8*(1-j)))&255)
 lines.append(''.join(f'{v:02x}' for v in vals))
(r/'data/fc3_quad_weights.mem').write_text('\n'.join(lines)+'\n')
p=d/'rtl/lab5_top.v';s=p.read_text().replace('.DSP_LANES(176)','.DSP_LANES(168)').replace('fc2_data_o, fc2_data_b_o,','fc2_data_o, fc2_data_b_o, fc2_data_c_o,fc2_data_d_o,').replace('.data_b_o(fc2_data_b_o),','.data_b_o(fc2_data_b_o),.data_c_o(fc2_data_c_o),.data_d_o(fc2_data_d_o),')
s=s.replace('.NI(16)','.NI(8)').replace('.IA(4),.OA(1)','.IA(3),.OA(1)').replace('fc3_dual_weights.mem','fc3_quad_weights.mem').replace('.data_b_i(fc2_data_b_o[34:0]),','.data_b_i(fc2_data_b_o[34:0]),.data_c_i(fc2_data_c_o[34:0]),.data_d_i(fc2_data_d_o[34:0]),').replace('fc2_addr_o[4:1]','fc2_addr_o[4:2]');p.write_text(s)
for p in [d/'tb/tb_lab5_top.v',d/'tb/tb_lab5_validation.v']:
 s=p.read_text().replace('d2,d2b;','d2,d2b,d2c,d2d;').replace('.fc2_data_b_o(d2b),','.fc2_data_b_o(d2b),.fc2_data_c_o(d2c),.fc2_data_d_o(d2d),')
 a=s.index('  if({{16{d2b');b=s.index('  n2=n2+1;',a)+len('  n2=n2+1;')
 s=s[:b]+'''\n  if({{16{d2c[47]}},d2c}!==ref2[n2])begin errors=errors+1;$display("MISMATCH FC2[%0d] %d",n2,$signed(d2c));end
  n2=n2+1;
  if({{16{d2d[47]}},d2d}!==ref2[n2])begin errors=errors+1;$display("MISMATCH FC2[%0d] %d",n2,$signed(d2d));end
  n2=n2+1;'''+s[b:];p.write_text(s)
for p in (d/'tools').glob('*.tcl'):
 s=p.read_text().replace(str(src),str(d)).replace(src.name+'.xpr',d.name+'.xpr').replace('create_project '+src.name,'create_project '+d.name);p.write_text(s)
print(d)
