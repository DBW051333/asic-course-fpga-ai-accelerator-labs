from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[1];V=Path('/vivado/2025.2/Vivado/bin')
mode=sys.argv[1] if len(sys.argv)>1 else 'axis'
name='tb_lab8' if mode=='axis' else 'tb_lab7'
bench=R/'tb'/('tb_lab8.sv' if mode=='axis' else 'tb_lab7_regression.sv')
D=R/'simulation'/mode;D.mkdir(parents=True,exist_ok=True);(D/'results').mkdir(exist_ok=True)
def call(args):
 p=subprocess.run([str(V/args[0]),*args[1:]],cwd=D,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (D/(args[0]+'.console.log')).write_text(p.stdout);print(p.stdout[-3500:]);p.check_returncode()
call(['xvlog','--sv',*[str(p) for p in sorted((R/'rtl').rglob('*.v'))],str(bench)])
call(['xelab',name,'-s','lab8_sim','-debug','typical','-mt','2'])
(D/'run.tcl').write_text('run all\nquit\n')
call(['xsim','lab8_sim','-tclbatch','run.tcl','-wdb','lab8.wdb'])
log=(D/'xsim.console.log').read_text();passed=('PASS LAB8 AXIS AXILITE' if mode=='axis' else 'PASS LAB7') in log and 'errors=0' in log
(R/'results'/f'simulation_{mode}.json').write_text(json.dumps({'pass':passed,'scope':'RTL AXIS/AXI-Lite + real NPU; DMA/PS not simulated' if mode=='axis' else 'unchanged Lab7 regression','summary':[s for s in log.splitlines() if s.startswith(('SUMMARY','PASS BATCH','BATCH count='))],'log':str(D/'xsim.console.log')},indent=2))
assert passed
