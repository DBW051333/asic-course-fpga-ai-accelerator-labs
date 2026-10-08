from pathlib import Path
import json,re,subprocess,sys
r=Path('/home/ding/vivado_project/Lab5_optimization');d=r/sys.argv[1];period=json.loads((d/'results/final_clock.json').read_text())['period']
p=d/'tb/tb_lab5_burst.v';s=p.read_text().replace('always #5 clk_i=~clk_i;',f'localparam real CLK_PERIOD={period};\nalways #(CLK_PERIOD/2) clk_i=~clk_i;').replace('launched=$time+5','launched=$realtime+CLK_PERIOD/2')
s=re.sub(r'localparam real CLK_PERIOD=[0-9.]+;',f'localparam real CLK_PERIOD={period};',s);s=re.sub(r'\b(?:real)*time launched;', 'realtime launched;',s)
p.write_text(s)
with (d/'results/burst_final_clock.log').open('w') as out:
 c=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source','tools/run_burst.tcl','-log','results/burst.log','-journal','results/burst.jou'],cwd=d,stdout=out,stderr=subprocess.STDOUT)
s=(d/'results/burst_final_clock.log').read_text();print(c.returncode);print('\n'.join(x for x in s.splitlines() if 'BURST job=' in x or 'PASS:' in x or 'MISMATCH' in x or 'FAIL' in x));assert 'PASS: six overlapping' in s
