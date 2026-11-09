from pathlib import Path
import subprocess, json, re

ROOT = Path(__file__).resolve().parents[1]
BASE = Path('/home/ding/vivado_project/Lab8_AX7020_192')
BIN = Path('/vivado/2025.2/Vivado/bin')
wrapper = ROOT / 'vivado/Lab8.gen/sources_1/bd/lab8_system/ip/lab8_system_axi_dma_0_0/sim/lab8_system_axi_dma_0_0.vhd'
results = {}
for name, batch in [('dma_parent', False), ('dma_candidate', True)]:
    run = ROOT / 'simulation' / name
    run.mkdir(parents=True, exist_ok=True)
    sources = sorted(((ROOT if batch else BASE) / 'rtl').rglob('*.v'))
    commands = [
        ['xvhdl', str(wrapper)],
        ['xvlog', '--sv', '--define', 'BATCH', *map(str, sources), str(ROOT / 'tb/tb_dma_schedule.sv'), '/vivado/2025.2/Vivado/data/verilog/src/glbl.v'],
        ['xelab', 'tb_dma_schedule', 'glbl', '-s', 'dma_schedule', '-debug', 'typical', '-mt', '2', '-L', 'axi_dma_v7_1_37', '-L', 'unisims_ver', '-L', 'unimacro_ver', '-L', 'secureip'],
        ['xsim', 'dma_schedule', '-tclbatch', 'run.tcl'],
    ]
    (run / 'run.tcl').write_text('run all\nquit\n')
    for command in commands:
        result = subprocess.run([str(BIN / command[0]), *command[1:]], cwd=run, capture_output=True, text=True)
        (run / f'{command[0]}.log').write_text(result.stdout + result.stderr)
        if result.returncode:
            print((result.stdout + result.stderr)[-4000:])
            raise RuntimeError(f'{name}: {command[0]} failed')
    log = (run / 'xsim.log').read_text()
    match = re.search(r'PASS DMA SCHEDULE samples=42 values=(\d+) total_cycles=(\d+) errors=0', log)
    if not match:
        print(log[-4000:])
        raise RuntimeError(f'{name}: no passing summary')
    results[name] = {'feature_values_checked': int(match.group(1)), 'total_cycles': int(match.group(2)), 'log': str(run / 'xsim.log')}
    print(name, match.group(0), flush=True)
(ROOT / 'results/dma_schedule.json').write_text(json.dumps({'scope': 'Actual configured AMD AXI DMA IP and stalled AXI memory model. Host register transactions are idealized, not ARM/Python measurements. Board/PS measurements unavailable.', 'results': results}, indent=2) + '\n')
