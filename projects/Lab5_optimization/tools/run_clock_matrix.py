from pathlib import Path
import shutil,subprocess,time,re,json
R=Path('/home/ding/vivado_project/Lab5_optimization')
trials=[('stream_pair171_staged',5.0),('stream_pair256_staged',6.0),('stream_pair256_staged',5.0),('stream_pair171_staged',4.5),('stream_pair256_staged',4.5)]
results=[]
for base,period in trials:
 src=R/base
 while not (src/'results/sim_console.log').exists() or 'PASS: three consecutive' not in (src/'results/sim_console.log').read_text():time.sleep(5)
 name=base+'_clk'+str(period).replace('.','p');dst=R/name
 for folder in ('rtl','tb','tools'):shutil.copytree(src/folder,dst/folder,dirs_exist_ok=True)
 (dst/'results').mkdir(exist_ok=True);(dst/'vivado').mkdir(exist_ok=True)
 shutil.copy2(src/'vivado'/f'{base}.xpr',dst/'vivado'/f'{base}.xpr')
 (dst/'timing.xdc').write_text(f'create_clock -period {period:.3f} [get_ports clk_i]\n')
 p=dst/'tools/run_impl.tcl';p.write_text(p.read_text().replace(str(src),str(dst)))
 with (dst/'results/impl_console.log').open('w') as out:
  result=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/run_impl.tcl','-log','results/impl.log','-journal','results/impl.jou'],cwd=dst,stdout=out,stderr=subprocess.STDOUT)
 p=dst/'results/timing_impl.rpt';wns=None
 if p.exists():
  m=re.search(r'Slack \([^)]*\)\s*:\s*(-?[\d.]+)ns',p.read_text());wns=float(m.group(1)) if m else None
 results.append(dict(name=name,period=period,exit=result.returncode,wns=wns))
 (R/'results/clock_trials.json').write_text(json.dumps(results,indent=2))
 print(results[-1],flush=True)
