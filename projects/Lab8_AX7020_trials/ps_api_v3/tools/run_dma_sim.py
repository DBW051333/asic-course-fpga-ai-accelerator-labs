from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parents[1];V=Path('/vivado/2025.2/Vivado/bin');D=R/'simulation/dma';D.mkdir(parents=True,exist_ok=True);(D/'results').mkdir(exist_ok=True)
def call(args):
 p=subprocess.run([str(V/args[0]),*args[1:]],cwd=D,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (D/(args[0]+'.console.log')).write_text(p.stdout);print(p.stdout[-2500:]);p.check_returncode()
wrapper=R/'vivado/Lab8.gen/sources_1/bd/lab8_system/ip/lab8_system_axi_dma_0_0/sim/lab8_system_axi_dma_0_0.vhd'
call(['xvhdl',str(wrapper)])
call(['xvlog','--sv',*[str(p) for p in sorted((R/'rtl').rglob('*.v'))],str(R/'tb/tb_lab8_dma.sv'),'/vivado/2025.2/Vivado/data/verilog/src/glbl.v'])
call(['xelab','tb_lab8_dma','glbl','-s','dma_sim','-debug','typical','-mt','2','-L','axi_dma_v7_1_37','-L','unisims_ver','-L','unimacro_ver','-L','secureip'])
(D/'run.tcl').write_text('log_wave /tb_lab8_dma/indata /tb_lab8_dma/inkeep /tb_lab8_dma/inlast /tb_lab8_dma/inv /tb_lab8_dma/inready /tb_lab8_dma/outdata /tb_lab8_dma/outkeep /tb_lab8_dma/outlast /tb_lab8_dma/outv /tb_lab8_dma/outready\nrun all\nquit\n')
call(['xsim','dma_sim','-tclbatch','run.tcl','-wdb','dma.wdb'])
log=(D/'xsim.console.log').read_text();passed='PASS LAB8 ACTUAL DMA' in log
(R/'results/simulation_dma.json').write_text(json.dumps({'pass':passed,'scope':'Actual configured AMD AXI DMA IP + Lab8 NPU; AXI DDR model and AXI-Lite PS transactions; no real PS or board','summary':[s for s in log.splitlines() if s.startswith('PASS LAB8')],'log':str(D/'xsim.console.log')},indent=2))
assert passed
