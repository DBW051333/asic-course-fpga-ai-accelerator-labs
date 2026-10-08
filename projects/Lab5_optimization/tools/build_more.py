from pathlib import Path
import re, shutil,ast
R=Path('/home/ding/vivado_project/Lab5_optimization')
base=(R/'rtl/fc1_paired.v').read_text()
s=base.replace('parameter WEIGHTS="",INPUTS="",BIASES=""','parameter LANES=128,GROUPS=4,ADDER_LANES=128,DSP_LANES=128,WEIGHTS="",INPUTS="",BIASES=""')
s=s.replace('[2047:0] weights[0:255]','[LANES*16-1:0] weights[0:64*GROUPS-1]').replace('[1023:0] inputs[0:3]','[LANES*8-1:0] inputs[0:GROUPS-1]')
s=s.replace('reg [7:0] issue_addr;','reg [7:0] issue_addr;reg [1:0] issue_group;reg [5:0] issue_pair;')
s=s.replace('[2047:0] weight_r;reg [1023:0] input_r;','[LANES*16-1:0] weight_r;reg [LANES*8-1:0] input_r;')
s=s.replace('[0:127]','[0:LANES-1]')
s=s.replace('(* use_dsp="yes" *) reg signed [32:0] product[0:LANES-1];','wire signed [32:0] product[0:LANES-1];reg signed [7:0] w0_p[0:LANES-1],w1_p[0:LANES-1];')
s=s.replace('wire [2047:0] low_bus,high_bus;','wire [ADDER_LANES*16-1:0] low_bus,high_bus;')
a=s.index('genvar g;generate');b=s.index(' adder_tree tree0',a)
s=s[:a]+'''genvar g;generate for(g=0;g<ADDER_LANES;g=g+1)begin:pack_bus
 if(g<LANES)begin
  assign low_bus[ADDER_LANES*16-1-g*16 -:16]=low_product[g];
  assign high_bus[ADDER_LANES*16-1-g*16 -:16]=high_product[g];
 end else begin
  assign low_bus[ADDER_LANES*16-1-g*16 -:16]=16'd0;
  assign high_bus[ADDER_LANES*16-1-g*16 -:16]=16'd0;
 end
 end
 for(g=0;g<LANES;g=g+1)begin:mult
  if(g<DSP_LANES)begin
   (* use_dsp="yes" *) reg signed [32:0] p;
   always @(posedge clk_i) p<=packed_w[g]*input_p[g];
   assign product[g]=p;
  end else begin
   (* use_dsp="no" *) reg signed [15:0] p0,p1;
   always @(posedge clk_i)begin p0<=w0_p[g]*input_p[g];p1<=w1_p[g]*input_p[g];end
   assign product[g]={p1[15],p1,p0};
  end
 end endgenerate
'''+s[b:]
s=s.replace('inputs[issue_addr[1:0]]','inputs[issue_group]').replace('j<128','j<LANES')
s=s.replace('2047-j*16','LANES*16-1-j*16').replace('2039-j*16','LANES*16-9-j*16').replace('1023-j*8','LANES*8-1-j*8')
s=s.replace('product[j]<=packed_w[j]*input_p[j];product_r[j]<=product[j];','w0_p[j]<=weight_r[LANES*16-9-j*16 -:8];w1_p[j]<=weight_r[LANES*16-1-j*16 -:8];product_r[j]<=product[j];')
s=s.replace('high_product[j]<=$signed(product_r[j][32:16])+{16\'d0,product_r[j][15]};','if(j<DSP_LANES) high_product[j]<=$signed(product_r[j][32:16])+{16\'d0,product_r[j][15]};else high_product[j]<=product_r[j][31:16];')
s=s.replace('issue_addr<=0;valid_pipe<=0;','issue_addr<=0;issue_group<=0;issue_pair<=0;valid_pipe<=0;')
s=s.replace('tag[0]<=issue_addr;','tag[0]<={issue_pair,issue_group};')
s=s.replace('running<=1;issue_addr<=0;','running<=1;issue_addr<=0;issue_group<=0;issue_pair<=0;')
s=s.replace('else if(running)begin if(issue_addr==255)running<=0;else issue_addr<=issue_addr+1\'b1;end',"else if(running)begin if(issue_addr==64*GROUPS-1)running<=0;else issue_addr<=issue_addr+1'b1;if(issue_group==GROUPS-1)begin issue_group<=0;issue_pair<=issue_pair+1'b1;end else issue_group<=issue_group+1'b1;end")
s=s.replace('tag[8][1:0]==3','tag[8][1:0]==GROUPS-1')
(R/'rtl/fc1_paired_generic.v').write_text(s)
# Load only tree generator function, not the project-generation loop.
tree_ast=ast.parse((R/'tools/build_variants.py').read_text());fn=next(n for n in tree_ast.body if isinstance(n,ast.FunctionDef) and n.name=='tree');scope={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'tree','exec'),scope);tree=scope['tree']
D=Path('/home/ding/vivado_project/Lab5/data/params')
def vals(p):
 z=p.read_text().split('memory_initialization_vector')[1].split('=',1)[1];return [int(x,2) for x in re.findall('[01]{8}',z)]
w=vals(D/'fc1.0.weight.coe');b=vals(D/'fc1.0.bias.coe')
z=Path('/home/ding/vivado_project/Lab5/data/input/sel_data_128.coe').read_text().split('memory_initialization_vector')[1].split('=',1)[1];inputs=[int(x,2) for x in re.findall('[01]{8}',z)];assert len(inputs)==512
for name,lanes,groups,dsp in [('stream_pair171',171,3,171),('stream_pair256_hybrid',256,2,176)]:
 d=R/name
 for n in ('rtl','tools','tb','results'):(d/n).mkdir(parents=True,exist_ok=True)
 for n in ('fc_stream.v','lab5_impl_top.v','tb_lab5_top.v'):shutil.copy2(R/'rtl'/n,d/('tb' if n.startswith('tb') else 'rtl')/n)
 (d/'rtl/fc1_paired.v').write_text(s)
 (d/'rtl/adder_tree.v').write_text(tree(256,[2,2,2,2]))
 mem=R/f'data/{name}_weights.mem'
 words=[]
 for pair in range(64):
  for group in range(groups):
   words.append(''.join(f'{w[(2*pair+1)*512+group*lanes+j]:02x}{w[(2*pair)*512+group*lanes+j]:02x}' if group*lanes+j<512 else '0000' for j in range(lanes)))
 mem.write_text('\n'.join(words)+'\n')
 inp=R/f'data/{name}_inputs.mem'
 inp.write_text('\n'.join(''.join(f'{inputs[g*lanes+j]:02x}' if g*lanes+j<512 else '00' for j in range(lanes)) for g in range(groups))+'\n')
 top=(R/'stream_pair128/rtl/lab5_top.v').read_text().replace('fc1_paired #(',f'fc1_paired #(.LANES({lanes}),.GROUPS({groups}),.ADDER_LANES(256),.DSP_LANES({dsp}),').replace(str(R/'data/fc1_paired_weights.mem'),str(mem)).replace(str(R/'data/fc1_inputs.mem'),str(inp));(d/'rtl/lab5_top.v').write_text(top)
 for n in ('create_sim.tcl','run_impl.tcl'):(d/'tools'/n).write_text((R/'stream_pair128/tools'/n).read_text().replace('stream_pair128',name))
 print(name)
