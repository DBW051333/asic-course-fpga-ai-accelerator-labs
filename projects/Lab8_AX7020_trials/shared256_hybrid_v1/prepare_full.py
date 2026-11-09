from pathlib import Path
import shutil,re
R=Path(__file__).resolve().parent;P=R/'baseline192';D=R/'hybrid256'
for s in ['rtl/core','data','results','tools','tb']:(D/s).mkdir(parents=True,exist_ok=True)
for f in (P/'data').glob('*.mem'):shutil.copy2(f,D/'data'/f.name)
for f in (P/'rtl/core').glob('*.v'):(D/'rtl/core'/f.name).write_text(f.read_text().replace(str(P),str(D)))
banks=[[int(s,16) for s in (P/f'data/fc1_bank{i}.mem').read_text().split()] for i in range(12)]
mask=(1<<25)-1
oldrows=[[((banks[l//16][p*3+g]>>((15-l%16)*25))&mask) for g in range(3) for l in range(192)][:512] for p in range(64)]
rows=[row[g*256:(g+1)*256] for row in oldrows for g in range(2)]
rows += [[((banks[l//16][a]>>((15-l%16)*25))&mask) if l<192 else 0 for l in range(256)] for a in range(192,209)]
assert len(rows)==145
for row in rows:
 for v in row:
  s=v-(1<<25) if v&(1<<24) else v
  assert -8388608<=s<=8388607, '24 bit guard failed'
for i in range(16):
 lines=[]
 for row in rows:
  v=0
  for x in row[i*16:(i+1)*16]:v=(v<<25)|x
  lines.append(f'{v:0100x}')
 lines+=['0'*100]*(256-len(lines));(D/f'data/fc1_bank{i}.mem').write_text('\n'.join(lines)+'\n')
f=D/'rtl/core/lab7_core.v';f.write_text(f.read_text().replace('.LANES(192),.GROUPS(3)','.LANES(256),.GROUPS(2)').replace('.DSP_LANES(192)','.DSP_LANES(220)'))
f=D/'rtl/core/fc1_paired.v';t=f.read_text()
a=t.index(' // 24 stripes');b=t.index(' (* rom_style="distributed" *) reg [15:0]',a)
t=t[:a]+' // 32 single-bank input stripes, two groups of 256 INT8 values.\n'+t[b:]
t=t.replace('ib<24','ib<32')
a=t.index('  wire [1:0] write_group=');b=t.index('  // Uniform single-address',a)
t=t[:a]+'''  wire [1:0] write_group=load_addr_i<32 ? 0 : 1;
  wire write_hit=load_addr_i==ib || load_addr_i==ib+32;
  wire [2:0] write_row={1'b0,write_group};
  wire [63:0] write_data=ordered;
'''+t[b:]
t=t.replace('issue_addr==191','issue_addr==127').replace("8'd192+issue_pair","8'd128+issue_pair").replace("8'd208","8'd144")
t=t.replace("{features1,512'd0}","{features1,1024'd0}").replace("{features2,1280'd0}","{features2,1792'd0}")
a=t.index('   wire signed [15:0] result[0:1];');b=t.index('\n  end\n end endgenerate',a)
t=t[:a]+'''   wire [15:0] y0,y1;
   packed_mul #(.METHOD(2)) lut_multiplier(.clk_i(clk_i),.ce_i(ce_i),.b(packed_w[g]),.x(input_p[g]),.y0(y0),.y1(y1));
   // Both paths have three multiplier registers; product_r supplies the common fourth stage.
   assign product[g]={y1[15],y1,y0};'''+t[b:]
# Remove obsolete generic LUT ROM / coefficient registers to keep intent explicit.
t=t.replace('wire signed [32:0] product[0:LANES-1];reg signed [7:0] w0_p[0:LANES-1],w1_p[0:LANES-1];','wire signed [32:0] product[0:LANES-1];')
a=t.index(' (* rom_style="distributed" *) reg signed [7:0] nibble_su');b=t.index(' generate if(LANES/16>0)',a);t=t[:a]+t[b:]
t=t.replace('w0_p[bi]<=weight_q[LANES*25-9-bi*25 -:8];w1_p[bi]<=weight_q[LANES*25-1-bi*25 -:8];','')
f.write_text(t);shutil.copy2(R/'packed_mul.v',D/'rtl/core/packed_mul.v')
# Independent reproducible checkers, with primitive models only passed to simulation.
O=R.parent/'shared192_singlebank_v1'
for n in ['verify_core.py','verify_stress.py','verify_mapped.py','export_netlists.tcl']:
 t=(O/n).read_text().replace("['independent','shared_pair']","['hybrid256']")
 t=t.replace("D=R/'independent/data'","D=R/'baseline192/data'")
 t=t.replace("str(V/args[0]),*args[1:]","str(V/args[0]),*args[1:]")
 if n in ['verify_core.py','verify_stress.py']:

  t=t.replace("['xvlog','--sv',", "['xvlog','--sv',str(R/'sim_primitives.v'),")
 (R/n).write_text(t)
print('prepared full candidate and model guard')
