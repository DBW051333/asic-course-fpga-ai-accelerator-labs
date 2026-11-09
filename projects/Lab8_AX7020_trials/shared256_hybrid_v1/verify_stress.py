from pathlib import Path
import subprocess,json,sys,random
R=Path(__file__).resolve().parent;V=Path('/vivado/2025.2/Vivado/bin');D=R/'baseline192/data'
def signed(v,n=8):return v-(1<<n) if v&(1<<(n-1)) else v
def unpack(v):
 a=signed(v&255);b=(signed(v,25)-a)//65536
 return a,b
banks=[[int(s,16) for s in (D/f'fc1_bank{i}.mem').read_text().split()] for i in range(12)]
w1=[[0]*512 for _ in range(128)]
for p in range(64):
 for g in range(3):
  for lane in range(192):
   i=g*192+lane
   if i>=512:continue
   a,b=unpack((banks[lane//16][p*3+g]>>((15-lane%16)*25))&((1<<25)-1));w1[2*p][i]=a;w1[2*p+1][i]=b
b1=[]
for s in (D/'fc1_paired_bias.mem').read_text().split():b1.extend([signed(int(s,16)&255),signed(int(s,16)>>8)])
w2=[[0]*128 for _ in range(32)]
for i,s in enumerate((D/'fc2_packed_weights.mem').read_text().split()):
 for p in range(16):w2[2*p][i],w2[2*p+1][i]=unpack((int(s,16)>>((15-p)*25))&((1<<25)-1))
w3=[[0]*32 for _ in range(2)]
for i,s in enumerate((D/'fc3_packed_weights.mem').read_text().split()):
 for g in range(4):w3[0][i*4+g],w3[1][i*4+g]=unpack((int(s,16)>>((3-g)*25))&((1<<25)-1))
b2=[signed(int(v,16)) for v in (D/'fc2_bias.mem').read_text().split()];b3=[signed(int(v,16)) for v in (D/'fc3_bias.mem').read_text().split()]
xs=[signed(int(v,16)) for v in (D/'inputs.mem').read_text().split()]
samples=[xs[i*512:(i+1)*512] for i in range(48)];rng=random.Random(20261020)
samples.extend([[-128]*512,[127]*512,[(-128 if i%2 else 127) for i in range(512)],[0]*512])
samples.extend([[rng.randrange(-128,128) for _ in range(512)] for _ in range(44)])
gold=[];fullgold=[];bound=[0,0,0]
for x in samples:
 for l,(ws,bs,shift) in enumerate([(w1,b1,10),(w2,b2,9),(w3,b3,8)]):
  sums=[sum(a*b for a,b in zip(x,w))+bias for w,bias in zip(ws,bs)];bound[l]=max(bound[l],max(abs(v) for v in sums))
  if l==0:fullgold.extend(max(v,0) for v in sums)
  out=[((max(v,0) if l<2 else v)>>shift)&255 for v in sums];gold.extend(out);x=[signed(v) for v in out]
assert gold[:7776]==[int(v,16) for v in (D/'features.mem').read_text().split()]
(R/'stress_inputs.mem').write_text(''.join(f'{v&255:02x}\n' for x in samples for v in x));(R/'stress_gold.mem').write_text(''.join(f'{v:02x}\n' for v in gold))
(R/'stress_fc1_full_gold.mem').write_text(''.join(f'{v:08x}\n' for v in fullgold))
for name in (sys.argv[1:] or ['hybrid256']):
 r=R/name;d=r/'simulation/stress';d.mkdir(parents=True,exist_ok=True)
 tb=(r/'simulation/core/tb.sv').read_text().replace('module tb_core;','module tb_stress;')
 tb=tb.replace('xs[0:24575],gold[0:7775]','xs[0:49151],gold[0:15551]').replace(str(r/'data/inputs.mem'),str(R/'stress_inputs.mem')).replace(str(r/'data/features.mem'),str(R/'stress_gold.mem')).replace('s<48','s<96').replace('samples=48','samples=96')
 # CE pause at falling edges, consume outputs only on enabled edges.
 tb=tb.replace('integer s,j,k,','reg [31:0] rng=32\'h10202026;integer stalls=0;integer s,j,k,')
 tb=tb.replace('if(v1)begin','if(ce && v1)begin').replace('if(v2)begin','if(ce && v2)begin').replace('if(v3)begin','if(ce && v3)begin').replace('while(!done)begin','while(!(done && ce))begin')
 tb=tb.replace('@(negedge clk);\nend\nif(n1','@(negedge clk);rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};ce=(rng[3:0]!=0 && rng[3:0]!=1);if(!ce)stalls=stalls+1;\nend\nce=1;\nif(n1')
 # Synchronous reset between selected samples, with stale activations left intact.
 tb=tb.replace('for(s=0;s<96;s=s+1)begin', '''for(s=0;s<96;s=s+1)begin
if(s==17 || s==49 || s==81)begin
 @(negedge clk);start=1;@(negedge clk);start=0;
 if(s==17)repeat(37)@(negedge clk);else if(s==49)repeat(155)@(negedge clk);else repeat(190)@(negedge clk);
 rst=0;ce=0;repeat(3)@(negedge clk);rst=1;ce=1;
end
if(s%13==0)begin @(negedge clk);rst=0;ce=0;repeat(3)@(negedge clk);rst=1;ce=1;end''')
 tb=tb.replace('$display("PASS CORE','$display("CE stalls=%0d",stalls);$display("PASS CORE')
 tb=tb.replace('reg[7:0] xs', 'reg[31:0] fullgold[0:12287];reg[7:0] xs')
 tb=tb.replace('initial begin\n$readmemh', 'initial begin\n$readmemh(\"'+str(R/'stress_fc1_full_gold.mem')+'\",fullgold);\n$readmemh')
 tb=tb.replace('if(ce && v1)begin', 'if(ce && v1)begin if(dut.u_fc1.fc_output_data_o!==fullgold[s*128+n1])$fatal(1,\"FC1 FULL s=%0d n=%0d\",s,n1);')
 (d/'tb.sv').write_text(tb)
 for args in [['xvlog','--sv',str(R/'sim_primitives.v'),*[str(f) for f in sorted((r/'rtl/core').glob('*.v'))],str(d/'tb.sv')],['xelab','tb_stress','-s','stress_sim','-mt','2'],['xsim','stress_sim','-runall']]:
  q=subprocess.run([str(V/args[0]),*args[1:]],cwd=d,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(d/(args[0]+'.log')).write_text(q.stdout);q.check_returncode()
 log=(d/'xsim.log').read_text();assert 'PASS CORE samples=96 values=15552' in log,log[-1500:]
 summary=[line for line in log.splitlines() if line.startswith(('PASS CORE','CE stalls='))]
 (r/'results/stress_verification.json').write_text(json.dumps({'pass':True,'samples':96,'values':15552,'fc1_full_precision_values':12288,'random_ce_stalls':True,'between_sample_reset':True,'aborted_job_reset_offsets_cycles':[37,155,190],'observed_max_absolute_accumulator':bound,'summary':summary},indent=2));print(name,summary,flush=True)
