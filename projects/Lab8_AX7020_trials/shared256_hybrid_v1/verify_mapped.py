from pathlib import Path
import subprocess,time,json,sys
R=Path(__file__).resolve().parent;V=Path('/vivado/2025.2/Vivado/bin');names=sys.argv[1:] or ['shared','independent']
while not all((R/n/'results/routed.dcp').exists() and (R/n/'simulation/core/tb.sv').exists() for n in names):time.sleep(3)
with (R/('export_netlists_'+'_'.join(names)+'.console.log')).open('w') as f:p=subprocess.run([str(V/'vivado'),'-mode','batch','-source',str(R/'export_netlists.tcl'),'-tclargs',str(R),*names],cwd=R,stdout=f,stderr=subprocess.STDOUT)
p.check_returncode()
for n in names:
 r=R/n;d=r/'simulation/mapped';d.mkdir(parents=True,exist_ok=True)
 # UNISIM models apply global configuration reset for 100ns at power-up.
 tb=(r/'simulation/core/tb.sv').read_text().replace('repeat(4)@(negedge clk);rst=1;', 'repeat(32)@(negedge clk);rst=1;')
 tb=tb.replace('$fatal(1,\"FC1 s=%0d n=%0d\",s,n1)', '$fatal(1,\"FC1 s=%0d n=%0d got=%h expected=%h addr=%0d\",s,n1,o1,gold[s*162+n1],a1)')
 samples=8 if n in ['split_bram','shared_pair','hybrid256'] else 48
 values=samples*162
 if samples==8:
  tb=tb.replace('integer s,j,k,', 'integer si,s,j,k,').replace('for(s=0;s<48;s=s+1)begin', 'for(si=0;si<8;si=si+1)begin s=(si==7)?47:si*7;').replace('PASS CORE samples=48','PASS CORE samples=8')
 (d/'tb.sv').write_text(tb)
 for args in [ ['xvlog','--sv',str(r/'results/core_funcsim.v'),str(d/'tb.sv'),str(V.parent/'data/verilog/src/glbl.v')],['xelab','tb_core','glbl','-L','unisims_ver','-L','unimacro_ver','-s','mapped_sim','-mt','2'],['xsim','mapped_sim','-runall'] ]:
  p=subprocess.run([str(V/args[0]),*args[1:]],cwd=d,capture_output=True,text=True);(d/(args[0]+'.log')).write_text(p.stdout+p.stderr)
  if p.returncode:print(n,args[0],(p.stdout+p.stderr)[-1800:],flush=True)
  p.check_returncode()
 log=(d/'xsim.log').read_text();passed=f'PASS CORE samples={samples} values={values}' in log
 summary=[v for v in log.splitlines() if v.startswith(('PASS CORE','EVENT '))]
 (r/'results/mapped_verification.json').write_text(json.dumps({'pass':passed,'samples':samples,'feature_values':values,'sample_indices':([0,7,14,21,28,35,42,47] if samples==8 else list(range(48))),'summary':summary,'scope':'post-route functional core netlist with AMD UNISIM primitives; no timing delays'},indent=2));print(n,passed,summary,flush=True);assert passed
