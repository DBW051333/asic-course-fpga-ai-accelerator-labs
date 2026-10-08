from pathlib import Path
import shutil
r=Path('/home/ding/vivado_project/Lab5_optimization');src=r/'stream_pair256_quadtail_clk5';d=r/'stream_pair256_eighttail_clk5';letters='abcdefgh'
for n in ['rtl','tb','tools']:shutil.copytree(src/n,d/n,dirs_exist_ok=True)
(d/'results').mkdir(exist_ok=True)
p=d/'rtl/fc_stream_pair_output.v';s=p.read_text().replace('data_c_o, data_d_o,','data_c_o, data_d_o, data_e_o,data_f_o,data_g_o,data_h_o,').replace('read_data_c,read_data_d;','read_data_c,read_data_d,read_data_e,read_data_f,read_data_g,read_data_h;')
s=s.replace("read_data_d<=acc[emit_idx+2'd3];","read_data_d<=acc[emit_idx+2'd3];"+''.join(f"read_data_{letters[k]}<=acc[emit_idx+3'd{k}];" for k in range(4,8)))
s=s.replace('NO-4','NO-8').replace("emit_idx+3'd4;","emit_idx+4'd8;")
template="            data_Z_o <= (RELU && read_data_Z[AW-1]) ? {OW{1'b0}} : {{(OW-AW){read_data_Z[AW-1]}},read_data_Z};\n"
s=s.replace('            done_o <=',''.join(template.replace('Z',c) for c in letters[4:])+'            done_o <=');p.write_text(s)
p=d/'rtl/fc_stream_two_inputs.v';s=p.read_text().replace('data_c_i, data_d_i,','data_c_i, data_d_i, data_e_i,data_f_i,data_g_i,data_h_i,').replace('NO*32','NO*64').replace('NO*4','NO*8')
s=s.replace('data_d_r,data_d_d;', 'data_d_r,data_d_d,'+','.join(f'data_{c}_r,data_{c}_d' for c in letters[4:])+';')
s=s.replace('reg signed [PW:0] sum_a [0:NO-1],sum_b [0:NO-1];\n    reg signed [PW+1:0] sum_r [0:NO-1];','reg signed [PW:0] sums1 [0:NO*4-1];\n    reg signed [PW+1:0] sums2 [0:NO*2-1];\n    reg signed [PW+2:0] sum_r [0:NO-1];')
s=s.replace('data_d_r<=data_d_i;','data_d_r<=data_d_i;'+''.join(f'data_{c}_r<=data_{c}_i;' for c in letters[4:])).replace('data_d_d<=data_d_r;','data_d_d<=data_d_r;'+''.join(f'data_{c}_d<=data_{c}_r;' for c in letters[4:]))
a=s.index('            product[j*4]');b=s.index('\n        end',a);body=''
for k,c in enumerate(letters):
 data='data_d' if k==0 else f'data_{c}_d'
 body+=f'            product[j*8+{k}]<={data}*$signed(weight_d[NO*64-{1+8*k}-j*64 -:8]);product_r[j*8+{k}]<=product[j*8+{k}];\n'
for k in range(4):body+=f'            sums1[j*4+{k}]<={{product_r[j*8+{2*k}][PW-1],product_r[j*8+{2*k}]}}+{{product_r[j*8+{2*k+1}][PW-1],product_r[j*8+{2*k+1}]}};\n'
for k in range(2):body+=f'            sums2[j*2+{k}]<={{sums1[j*4+{2*k}][PW],sums1[j*4+{2*k}]}}+{{sums1[j*4+{2*k+1}][PW],sums1[j*4+{2*k+1}]}};\n'
body+='            sum_r[j]<={sums2[j*2][PW+1],sums2[j*2]}+{sums2[j*2+1][PW+1],sums2[j*2+1]};'
s=s[:a]+body+s[b:];s=s.replace('[5:0] valid_pipe','[6:0] valid_pipe').replace('[4:0]','[5:0]').replace('pipe[5]','pipe[6]').replace('{{(AW-PW-2){sum_r[j][PW+1]}},sum_r[j]}','sum_r[j][AW-1:0]');p.write_text(s)
a=[int(x,16) for x in (r/'data/fc3_weights.mem').read_text().split()]
(r/'data/fc3_eight_weights.mem').write_text('\n'.join(''.join(f'{(a[i*8+k]>>(8*(1-j)))&255:02x}' for j in range(2) for k in range(8)) for i in range(4))+'\n')
p=d/'rtl/lab5_top.v';s=p.read_text().replace('.DSP_LANES(168)','.DSP_LANES(152)').replace('fc2_data_d_o,','fc2_data_d_o,fc2_data_e_o,fc2_data_f_o,fc2_data_g_o,fc2_data_h_o,')
s=s.replace('.data_d_o(fc2_data_d_o),','.data_d_o(fc2_data_d_o),'+''.join(f'.data_{c}_o(fc2_data_{c}_o),' for c in letters[4:]))
s=s.replace('.NI(8)','.NI(4)').replace('.IA(3),.OA(1)','.IA(2),.OA(1)').replace('fc3_quad_weights.mem','fc3_eight_weights.mem').replace('.data_d_i(fc2_data_d_o[34:0]),','.data_d_i(fc2_data_d_o[34:0]),'+''.join(f'.data_{c}_i(fc2_data_{c}_o[34:0]),' for c in letters[4:])).replace('fc2_addr_o[4:2]','fc2_addr_o[4:3]');p.write_text(s)
for p in [d/'tb/tb_lab5_top.v',d/'tb/tb_lab5_validation.v']:
 s=p.read_text().replace('d2c,d2d;','d2c,d2d,d2e,d2f,d2g,d2h;').replace('.fc2_data_d_o(d2d),','.fc2_data_d_o(d2d),'+''.join(f'.fc2_data_{c}_o(d2{c}),' for c in letters[4:]))
 a=s.index('  if({{16{d2d');b=s.index('  n2=n2+1;',a)+len('  n2=n2+1;')
 s=s[:b]+''.join(f'\n  if({{{{16{{d2{c}[47]}}}},d2{c}}}!==ref2[n2])begin errors=errors+1;$display("MISMATCH FC2[%0d] %d",n2,$signed(d2{c}));end\n  n2=n2+1;' for c in letters[4:])+s[b:];p.write_text(s)
for p in (d/'tools').glob('*.tcl'):
 s=p.read_text().replace(str(src),str(d)).replace(src.name+'.xpr',d.name+'.xpr').replace('create_project '+src.name,'create_project '+d.name);p.write_text(s)
print(d)
