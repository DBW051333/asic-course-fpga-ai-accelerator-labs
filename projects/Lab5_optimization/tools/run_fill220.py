from pathlib import Path
import subprocess,shutil,re,time,os
r=Path('/home/ding/vivado_project/Lab5_optimization');src=r/'stream_pair256_localinput_unbanked_exact23_tree7_clk4p8'
while not (src/'results/final_clock.json').exists():time.sleep(5)
d=r/'stream_pair256_fill220_exact23_tree7_clk4p8'
for n in ['rtl','tb','tools']:shutil.copytree(src/n,d/n,dirs_exist_ok=True)
(d/'results').mkdir(exist_ok=True)
p=src/'results/critical_paths.rpt';paths=p.read_text() if p.exists() else (src/'results/timing_final.rpt').read_text()
lanes=[]
for v in re.findall(r'Destination:\s+\S*mult\[(\d+)\]\.half',paths):
 k=int(v)
 if k>=168 and k not in lanes:lanes.append(k)
for k in range(168,256):
 if k not in lanes:lanes.append(k)
lanes=lanes[:4]
p=d/'rtl/fc1_paired.v';s=p.read_text().replace('if(g<DSP_LANES)', 'if(g<DSP_LANES'+''.join(f' || g=={k}' for k in lanes)+')').replace('if(j<DSP_LANES)', 'if(j<DSP_LANES'+''.join(f' || j=={k}' for k in lanes)+')');p.write_text('// Fill all 220 device DSPs: additional FC1 lanes '+str(lanes)+'\n'+s)
(d/'results/extra_dsp_lanes.txt').write_text(str(lanes)+'\n')
for p in (d/'tools').glob('*.tcl'):
 s=p.read_text().replace(str(src),str(d)).replace(src.name+'.xpr',d.name+'.xpr').replace('create_project '+src.name,'create_project '+d.name);p.write_text(s)
for phase,script in [('sim','create_sim.tcl'),('burst','run_burst.tcl'),('validation','run_final_validation.tcl')]:
 with (d/f'results/{phase}_console.log').open('w') as out:
  c=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/'+script,'-log',f'results/{phase}.log','-journal',f'results/{phase}.jou'],cwd=d,stdout=out,stderr=subprocess.STDOUT)
 assert c.returncode==0 and 'PASS:' in (d/f'results/{phase}_console.log').read_text()
print('220 DSP logical checks passed',lanes,flush=True)
# Finish the ongoing Explore comparison before starting another heavy flow.
while True:
 try:os.kill(770929,0)
 except ProcessLookupError:break
 time.sleep(5)
p=d/'tools/run_impl.tcl';s='set_param general.maxThreads 4\n'+p.read_text().replace('-jobs 2','-jobs 1');(d/'tools/run_serial_impl.tcl').write_text(s)
with (d/'results/impl_console.log').open('w') as out:
 c=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/run_serial_impl.tcl','-log','results/impl_serial.log','-journal','results/impl_serial.jou'],cwd=d,stdout=out,stderr=subprocess.STDOUT)
print('220 DSP route',c.returncode,flush=True)
if (d/'results/timing_impl.rpt').exists():subprocess.run(['python',str(r/'tools/finalize_clock.py'),d.name],cwd=r)
subprocess.run(['python',str(r/'tools/write_report.py')],cwd=r)
