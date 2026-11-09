from pathlib import Path
import json,shutil,hashlib
R=Path(__file__).resolve().parent;P=R.parent/'shared192_singlebank_v1/shared_pair'
(R/'kernels').mkdir(exist_ok=True)
# Freeze exact branch baseline source/data and inherited implementation evidence.
b=R/'baseline192'
if not b.exists():
 for sub in ['rtl/core','data','results']:
  (b/sub).mkdir(parents=True,exist_ok=True)
  for f in (P/sub).glob('*'):
   if not f.is_file():continue
   if sub=='results' and f.suffix not in ['.json','.rpt','.txt','.dcp']:continue
   if sub.startswith('rtl'):(b/sub/f.name).write_text(f.read_text().replace(str(P),str(b)))
   else:shutil.copy2(f,b/sub/f.name)
 original={str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for sub in ['rtl/core','data','results'] for f in (P/sub).glob('*') if f.is_file() and (sub!='results' or f.suffix in ['.json','.rpt','.txt','.dcp'])}
 (R/'baseline_identity.json').write_text(json.dumps({'id':'lab8_ax7020_shared192_v1','direct_source':str(P),'source_baseline':'lab8_128_resource_v1','core_cycles':264,'clock_ns':7,'lut':9057,'ff':22203,'bram36':72,'dsp':192,'verification_scope':'copied original source and inherited routed OOC evidence; paths rebased only; not a new build or board deployment','source_sha256':original},indent=2))
rtl='''`timescale 1ns/1ps
// LUT6_2 generate/add, exact signed radix4 partial product; M+2-bit modular accumulator.
module packed_ga #(parameter M=24)(input wire [M-1:0] a,input wire [2:0] digit,input wire [M+1:0] acc,output wire [M+1:0] sum);
 localparam N=M+2,C=((N+3)/4)*4;
 wire [C-1:0] pr,ge,co,oo;
 generate for(genvar i=0;i<M+1;i=i+1)begin:g
  wire xi=(i<M)?a[i]:a[M-1];
  wire xm=(i==0)?1'b0:((i<=M)?a[i-1]:a[M-1]);
  LUT6_2 #(.INIT(64'h0aac355ff553caa0)) u(.I0(xi),.I1(xm),.I2(digit[0]),.I3(digit[1]),.I4(digit[2]),.I5(acc[i]),.O5(ge[i]),.O6(pr[i]));
 end
 endgenerate
 // Arithmetic-shifted accumulator top2 bits and multiplicand sign extension coincide.
 assign pr[M+1]=pr[M];assign ge[M+1]=ge[M];
 generate if(C>N)begin assign pr[C-1:N]=0;assign ge[C-1:N]=0;end
 for(genvar j=0;j<C/4;j=j+1)begin:c
  CARRY4 u(.CI(j==0?1'b0:co[j*4-1]),.CYINIT(j==0?digit[2]:1'b0),.DI(ge[j*4+:4]),.S(pr[j*4+:4]),.CO(co[j*4+:4]),.O(oo[j*4+:4]));
 end endgenerate
 assign sum=oo[N-1:0];
endmodule
module packed_mul #(parameter METHOD=0)(input wire clk_i,ce_i,input wire signed [24:0] b,input wire signed [7:0] x,output wire [15:0] y0,y1);
 generate if(METHOD==0)begin:generic25
  (* use_dsp="no" *) reg signed [32:0] p;
  reg signed [32:0] q,r;
  always @(posedge clk_i)if(ce_i)begin p<=b*x;q<=p;r<=q;end
  assign y0=r[15:0];assign y1=$signed(r[32:16])+r[15];
 end else if(METHOD==1)begin:booth24
  wire [25:0] z0,z1,z2,z3;reg [25:0] z1d;reg [1:0] low;reg [23:0] ad;reg [4:0] xd;reg [31:0] result,delayed;
  packed_ga #(.M(24)) s0(b[23:0],{x[1:0],1'b0},26'd0,z0);
  packed_ga #(.M(24)) s1(b[23:0],x[3:1],{{2{z0[25]}},z0[25:2]},z1);
  packed_ga #(.M(24)) s2(ad,xd[2:0],{{2{z1d[25]}},z1d[25:2]},z2);
  packed_ga #(.M(24)) s3(ad,xd[4:2],{{2{z2[25]}},z2[25:2]},z3);
  always @(posedge clk_i)if(ce_i)begin ad<=b[23:0];xd<=x[7:3];z1d<=z1;low<=z0[1:0];result<={z3,z2[1:0],z1d[1:0],low};delayed<=result;end
  assign y0=delayed[15:0];assign y1=$signed(delayed[31:16])+delayed[15];
 end else begin:packed_sparse
  // Recode packed B, discard exactly-zero digits4..7. Keep the cross-band Booth bit B15.
  // This is a sparse 24x8 packed multiplication, not two decoded ordinary coefficients.
  reg [7:0] xd;
  always @(posedge clk_i)if(ce_i)xd<=x;
  for(genvar h=0;h<2;h=h+1)begin:band
   wire [7:0] w=h==0?b[7:0]:b[23:16];
   wire previous=h==0?1'b0:b[15];
   wire [9:0] z0,z1,z2,z3;reg [9:0] z1d;reg [1:0] low;reg [4:0] wd;reg [15:0] result,delayed;
   packed_ga #(.M(8)) s0(x,{w[1:0],previous},10'd0,z0);
   packed_ga #(.M(8)) s1(x,w[3:1],{{2{z0[9]}},z0[9:2]},z1);
   packed_ga #(.M(8)) s2(xd,wd[2:0],{{2{z1d[9]}},z1d[9:2]},z2);
   packed_ga #(.M(8)) s3(xd,wd[4:2],{{2{z2[9]}},z2[9:2]},z3);
   always @(posedge clk_i)if(ce_i)begin z1d<=z1;low<=z0[1:0];wd<=w[7:3];result<={z3,z2[1:0],z1d[1:0],low};delayed<=result;end
   if(h==0)assign y0=delayed;else assign y1=delayed;
  end
 end endgenerate
endmodule
'''
(R/'packed_mul.v').write_text(rtl)
for method,name in enumerate(['generic25','booth24','packed_sparse']):
 d=R/'kernels'/name;(d/'rtl').mkdir(parents=True,exist_ok=True);(d/'results').mkdir(exist_ok=True)
 (d/'rtl/packed_mul.v').write_text(rtl)
 (d/'rtl/kernel.v').write_text('''module kernel(input wire clk_i,ce_i,input wire [287:0] x_i,input wire [899:0] b_i,output reg [575:0] y0_o,y1_o);
reg [287:0] x;reg [899:0] b;wire [575:0] y0,y1;
always @(posedge clk_i)if(ce_i)begin x<=x_i;b<=b_i;y0_o<=y0;y1_o<=y1;end
generate for(genvar i=0;i<36;i=i+1)begin:g
packed_mul #(.METHOD(METHODVALUE)) u(clk_i,ce_i,b[i*25+:25],x[i*8+:8],y0[i*16+:16],y1[i*16+:16]);end endgenerate
endmodule
'''.replace('METHODVALUE',str(method)))
(R/'experiment.json').write_text(json.dumps({'id':'lab8_ax7020_shared256_hybrid_v1','direct_parent':'lab8_ax7020_shared192_v1','parent_path':str(P),'source_baseline':'lab8_128_resource_v1','target':'AX7020 xc7z020clg400-2','clock_ns':7,'user_authorization':'2026-10-20 user explicitly requested 256 packed lanes:220 DSP plus36 specialized LUT units; this supersedes earlier no-LUT/keep192 rules for this independent trial only. 512 deferred.','primary_metric':'same-clock single-sample whole-core latency, expected264->200 cycles (24.24% less), actual implementation required','selection':'compare36-lane packed25/24 LUT kernels, require0DSP and exact output, II1, same3 multiplier pipeline cycles pluscommonIO registers; select low-LUT candidate meeting7ns','budget':'three existing-literature-informed soft-multiplier structures, one selected complete256 three-layer design with required integration/timing repairs; no model changes or512 implementation','scope_target':'complete three-layer core, single-bank CMD1/CMD2 NPU wrapper, PS/DMA Vivado full system and reproducible deployment artifacts if implementation passes; board test reported separately'},indent=2,ensure_ascii=False))
# Simulation-only Xilinx behavioral primitive descriptions, never read into synthesis.
shutil.copy2(R.parent/'fc1_int8_multiplier_ab_v1/simulation/primitives.v',R/'sim_primitives.v')
print('Prepared baseline and three 36-lane kernels')
