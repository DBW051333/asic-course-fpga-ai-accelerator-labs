from pathlib import Path
import sys,json,subprocess,re
r=Path('/home/ding/vivado_project/Lab5_optimization');d=r/sys.argv[1];period=json.loads((d/'results/final_clock.json').read_text())['period']
p=d/'tb/tb_lab5_validation.v';s=p.read_text().replace('always #5 clk_i=~clk_i;',f'localparam real CLK_PERIOD={period};\nalways #(CLK_PERIOD/2) clk_i=~clk_i;').replace('launched=$time+5','launched=$realtime+CLK_PERIOD/2').replace('$time-launched','$realtime-launched').replace('elapsed_ns=%0d','elapsed_ns=%0.3f').replace('($realtime-launched)/10','$rtoi(($realtime-launched)/CLK_PERIOD+0.001)')
s=re.sub(r"localparam real CLK_PERIOD=[0-9.]+;",f"localparam real CLK_PERIOD={period};",s)
s=re.sub(r'\b(?:real)*time launched;', 'realtime launched;',s)
p.write_text(s)
with (d/'results/validation_final_clock.log').open('w') as out:
 c=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/run_final_validation.tcl','-log','results/validation.log','-journal','results/validation.jou'],cwd=d,stdout=out,stderr=subprocess.STDOUT)
print(c.returncode)
print('\n'.join(x for x in (d/'results/validation_final_clock.log').read_text().splitlines() if 'PASS:' in x or 'MEASURE' in x or 'FAIL' in x))
