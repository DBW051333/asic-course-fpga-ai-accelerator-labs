from pathlib import Path
p=Path('/home/ding/vivado_project/Lab6_growth_trials/tail8')
f=p/'rtl/lab5_top.v';f.write_text(f.read_text().replace('.DSP_LANES(200)','.DSP_LANES(196)'))
def conv(v):
 w0=v&255; s0=w0 if w0<128 else w0-256
 w1=((v>>16)+int(s0<0))&255
 return ((w1<<8)|w0)<<9
for name,width,positions in [('fc1_bank12.mem',400,range(4,8)),('fc1_prepacked.mem',6400,range(196,200))]:
 f=p/'data'/name
 if not f.exists():continue
 out=[]
 for line in f.read_text().splitlines():
  v=int(line,16)
  for i in positions:
   shift=width-25*(i+1); old=(v>>shift)&((1<<25)-1)
   v=(v&~(((1<<25)-1)<<shift))|(conv(old)<<shift)
  out.append(f'{v:0{width//4}x}')
 f.write_text('\n'.join(out)+'\n')
