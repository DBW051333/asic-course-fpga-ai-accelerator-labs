from pathlib import Path
import shutil
R=Path(__file__).resolve().parent;D=R/'hybrid256';P=Path('/home/ding/vivado_project/Lab8_optimization_trials/fc1_128_groups4');A=Path('/home/ding/vivado_project/Lab8_AX7020_192')
for sub in ['overlay','tools','ps','results','tb']:(D/sub).mkdir(exist_ok=True)
for f in (P/'rtl').glob('*.v'):shutil.copy2(f,D/'rtl'/f.name)
# Same already-verified CMD1/CMD2 single-bank transport, no experimental batch prototype.
for f in (P/'tb').glob('*.sv'):(D/'tb'/f.name).write_text(f.read_text().replace(str(P),str(D)).replace('303','200'))
for n in ['build.tcl','export_results.tcl','postroute_opt.tcl','audit_dsp.tcl']:shutil.copy2(A/'tools'/n,D/'tools'/n)
shutil.copy2(A/'control_routing.xdc',D/'control_routing.xdc')
for f in (P/'ps').glob('*'):
 if f.is_file():shutil.copy2(f,D/'ps'/f.name)
print('prepared single-bank CMD1/CMD2 system; AX7020 DDR/PS configuration')
