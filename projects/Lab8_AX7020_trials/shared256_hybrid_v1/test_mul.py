from pathlib import Path
import subprocess
R=Path(__file__).resolve().parent
S=R/'mul_test';S.mkdir(exist_ok=True)
(S/'test_top.v').write_text('module test_top(input clk_i,ce_i,input signed[24:0] b,input signed[7:0] x,output[31:0] a,c,d);\n'+''.join(f'packed_mul #(.METHOD({i})) m{i}(clk_i,ce_i,b,x,{n}[15:0],{n}[31:16]);\n' for i,n in enumerate('acd'))+'endmodule\n')
(S/'main.cpp').write_text(r'''
#include "Vtest_top.h"
#include "verilated.h"
#include <cstdio>
#include <cstdint>
#include <deque>
int main(int argc,char**argv){Verilated::commandArgs(argc,argv);Vtest_top t;std::deque<uint32_t> q;uint64_t n=0;uint32_t rng=33;
auto tick=[&](int w0,int w1,int x){int32_t b=w1*65536+w0;uint32_t e=(uint16_t)(w0*x)|((uint32_t)(uint16_t)(w1*x)<<16);t.b=b&0x1ffffff;t.x=x&255;rng=rng*1664525+1013904223;
if((rng&1023)==0){auto a=t.a,c=t.c,d=t.d;t.ce_i=0;t.clk_i=0;t.eval();t.clk_i=1;t.eval();if(t.a!=a||t.c!=c||t.d!=d){puts("CE FAIL");exit(2);}}
t.ce_i=1;t.clk_i=0;t.eval();t.clk_i=1;t.eval();q.push_back(e);if(q.size()>=3){auto r=q.front();q.pop_front();if(t.a!=r||t.c!=r||t.d!=r){printf("FAIL n=%llu a=%08x c=%08x d=%08x expected=%08x\n",(unsigned long long)n,t.a,t.c,t.d,r);exit(3);}}n++;};
for(int w1=-128;w1<128;w1++)for(int w0=-128;w0<128;w0++){int b=w1*65536+w0;if(b < -8388608 || b>8388607)continue;for(int x=-128;x<128;x++)tick(w0,w1,x);}
tick(0,0,0);tick(0,0,0);printf("PASS %llu triples plus randomized CE stalls\n",(unsigned long long)n-2);}
''')
cmd=['verilator','--cc','--exe','--build','-j','4','-O3','-Wno-fatal','--top-module','test_top','--Mdir',str(S/'obj'),str(R/'sim_primitives.v'),str(R/'packed_mul.v'),str(S/'test_top.v'),str(S/'main.cpp')]
with (S/'build.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
p=subprocess.run([str(S/'obj/Vtest_top')],capture_output=True,text=True);(S/'result.log').write_text(p.stdout+p.stderr);print(p.stdout);p.check_returncode()
