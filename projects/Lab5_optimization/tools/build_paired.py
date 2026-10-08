from pathlib import Path
import sys,shutil,re
sys.path.insert(0,str(Path(__file__).parent))
# Import generated common matrix/partition utilities without overwriting active projects.
R=Path('/home/ding/vivado_project/Lab5_optimization');D=Path('/home/ding/vivado_project/Lab5/data/params')
def vals(p):
 s=p.read_text().split('memory_initialization_vector')[1].split('=',1)[1];return re.findall('[01]{8}',s)
w=vals(D/'fc1.0.weight.coe');b=vals(D/'fc1.0.bias.coe')
words=[]
for pair in range(64):
 for group in range(4):
  words.append(''.join(f'{int(w[(2*pair+1)*512+group*128+j],2):02x}{int(w[(2*pair)*512+group*128+j],2):02x}' for j in range(128)))
(R/'data/fc1_paired_weights.mem').write_text('\n'.join(words)+'\n')
(R/'data/fc1_paired_bias.mem').write_text('\n'.join(f'{int(b[2*p+1],2):02x}{int(b[2*p],2):02x}' for p in range(64))+'\n')
s=Path('/home/ding/vivado_project/Lab5/data/input/sel_data_128.coe').read_text().split('memory_initialization_vector')[1].split('=',1)[1]
words=re.findall('[01]{1024}',s)
assert len(words)==4
(R/'data/fc1_inputs.mem').write_text('\n'.join(f'{int(v,2):0256x}' for v in words)+'\n')
root=R/'stream_pair128'
for n in ('rtl','tb','tools','results'):(root/n).mkdir(parents=True,exist_ok=True)
for n in ('fc_stream.v','lab5_impl_top.v','tb_lab5_top.v'):
 shutil.copy2(R/'rtl'/n,root/('tb' if n.startswith('tb') else 'rtl')/n)
shutil.copy2(R/'rtl/fc1_paired.v',root/'rtl/fc1_paired.v')
shutil.copy2(R/'stream128_tree4/rtl/adder_tree.v',root/'rtl/adder_tree.v')
top=(R/'stream128_exact/rtl/lab5_top.v').read_text()
start=top.index('fc_top u_fc1(');end=top.index('\n',start)
top=top[:start]+f'fc1_paired #(.WEIGHTS("{R}/data/fc1_paired_weights.mem"),.INPUTS("{R}/data/fc1_inputs.mem"),.BIASES("{R}/data/fc1_paired_bias.mem")) u_fc1(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.done_o(d1),.fc_output_wren_o(fc1_wren_o),.fc_output_data_o(fc1_data_o),.fc_output_addr_o(fc1_addr_o));'+top[end:]
(root/'rtl/lab5_top.v').write_text(top)
create=(R/'stream128_exact/tools/create_sim.tcl').read_text().replace('stream128_exact','stream_pair128')
create='\n'.join(line for line in create.splitlines() if not line.startswith('add_files [list'))+'\n'
(root/'tools/create_sim.tcl').write_text(create)
run=(R/'stream128_exact/tools/run_impl.tcl').read_text().replace('stream128_exact','stream_pair128')
(root/'tools/run_impl.tcl').write_text(run)
print(root)
