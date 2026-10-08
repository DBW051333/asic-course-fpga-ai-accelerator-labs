from pathlib import Path
import ast,shutil
r=Path('/home/ding/vivado_project/Lab5_optimization');src=r/'stream_pair256_staged';d=r/'stream_pair256_partial5_clk5'
for n in ('rtl','tb','tools'):shutil.copytree(src/n,d/n,dirs_exist_ok=True)
(d/'results').mkdir(exist_ok=True)
p=d/'rtl/fc1_paired.v';s=p.read_text()
a=s.index('  if(g<DSP_LANES)begin');b=s.index(' end endgenerate',a)
s=s[:a]+'''  if(g<DSP_LANES)begin
   (* use_dsp="yes" *) reg signed [32:0] p;
   reg signed [32:0] d0,d1;
   always @(posedge clk_i)begin p<=packed_w[g]*input_p[g];d0<=p;d1<=d0;end
   assign product[g]=d1;
  end else begin
   wire signed [15:0] result[0:1];
   for(genvar h=0;h<2;h=h+1)begin:half
    wire signed [7:0] w=(h==0)?w0_p[g]:w1_p[g];
    (* use_dsp="no" *) reg [7:0] pp00;
    (* use_dsp="no" *) reg signed [7:0] pp01,pp10,pp11;
    reg signed [8:0] cross_r;
    reg signed [15:0] outer_r,p;
    always @(posedge clk_i)begin
     pp00<=input_p[g][3:0]*w[3:0];
     pp01<=$signed(input_p[g][7:4])*$signed({1'b0,w[3:0]});
     pp10<=$signed({1'b0,input_p[g][3:0]})*$signed(w[7:4]);
     pp11<=$signed(input_p[g][7:4])*$signed(w[7:4]);
     cross_r<={pp01[7],pp01}+{pp10[7],pp10};
     outer_r<={8'd0,pp00}+($signed({{8{pp11[7]}},pp11})<<<8);
     p<=outer_r+($signed({{7{cross_r[8]}},cross_r})<<<4);
    end
    assign result[h]=p;
   end
   assign product[g]={result[1][15],result[1],result[0]};
  end
'''+s[b:]
s=s.replace('reg [8:0] valid_pipe;reg [7:0] tag[0:8]','reg [11:0] valid_pipe;reg [7:0] tag[0:11]').replace('tag[8]','tag[11]').replace('valid_pipe[7:0]','valid_pipe[10:0]').replace('j<9','j<12').replace('valid_pipe[8])','valid_pipe[11])');p.write_text(s)
a=ast.parse((r/'tools/build_variants.py').read_text());fn=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='tree');ctx={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'tree','exec'),ctx)
(d/'rtl/adder_tree.v').write_text(ctx['tree'](256,[2,2,2,1,1]))
for p in (d/'tools').glob('*.tcl'):
 s=p.read_text().replace(str(src),str(d)).replace('create_project stream_pair256_staged','create_project '+d.name).replace('/vivado/stream_pair256_staged.xpr','/vivado/'+d.name+'.xpr').replace('-period 10.000','-period 5.000');p.write_text(s)
# Check signed nibble decomposition for every input/coefficient pair.
for a in range(-128,128):
 for b in range(-128,128):
  al=a&15;ah=a>>4;bl=b&15;bh=b>>4
  assert al*bl+((ah*bl+al*bh)<<4)+(ah*bh<<8)==a*b
(r/'results/nibble_decomposition_proof.txt').write_text('PASS: all 65,536 signed 8x8 products decompose exactly into four 4x4 partial products.\n')
print(d)
