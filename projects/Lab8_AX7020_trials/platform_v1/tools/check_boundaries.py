from pathlib import Path
import json,sys,subprocess,importlib.util
R=Path(__file__).resolve().parents[1];D=R/'simulation/boundaries';D.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('host_fakes',R/'tools/test_ps.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with m.device() as n:
 n.prepare_batch(16383)
 assert n.batch_tx.size==8+16383*512 and n.batch_rx.size==16383*8
 assert n.batch_tx.size<(1<<23)
 for bad in [0,16384]:
  try:n.prepare_batch(bad)
  except ValueError:pass
  else:raise AssertionError('out of range accepted')
s='''`timescale 1ns/1ps
module tb_boundaries;
reg clk=0,rst=0;always #3.5 clk=~clk;
reg [63:0] data=0;reg valid=0;wire ready;
lab7_top dut(.clk_i(clk),.rst_n_i(rst),.input_data_i(data),.input_valid_i(valid),.input_ready_o(ready),.output_ready_i(1'b1));
initial begin
 repeat(3)@(negedge clk);rst=1;
 @(negedge clk);data={32'd16383,32'd3};valid=1;
 @(posedge clk);while(!ready)@(posedge clk);
 @(negedge clk);valid=0;repeat(6)@(negedge clk);
 if(dut.batch_size!==14'd16383 || !dut.receiving || dut.state_r!=1)$fatal(1,"maximum header rejected");
 rst=0;repeat(3)@(negedge clk);rst=1;repeat(2)@(negedge clk);
 if(dut.receiving || dut.batch_size!=0)$fatal(1,"reset after maximum header failed");
 $display("PASS BOUNDARY maximum=16383 reset=ok");$finish;
end
initial begin #10000;$fatal(1,"watchdog");end
endmodule
'''
(D/'tb_boundaries.sv').write_text(s);V=Path('/vivado/2025.2/Vivado/bin')
for cmd in [['xvlog','--sv',*[str(p) for p in sorted((R/'rtl').rglob('*.v'))],str(D/'tb_boundaries.sv')],['xelab','tb_boundaries','-s','boundaries','-mt','2'],['xsim','boundaries','-runall']]:
 p=subprocess.run([str(V/cmd[0]),*cmd[1:]],cwd=D,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(D/(cmd[0]+'.log')).write_text(p.stdout);p.check_returncode()
assert 'PASS BOUNDARY' in (D/'xsim.log').read_text()
(R/'results/boundary_checks.json').write_text(json.dumps({'pass':True,'max_batch':16383,'max_tx_bytes':8+16383*512,'dma_length_bits':23,'host_allocation_limit_checked':True,'rtl_max_header_and_reset_checked':True,'zero_and_overlimit':'covered by existing RTL regression and host tests','scope':'protocol/driver boundary only; no full 16383 sample run'},indent=2))
print('PASS maximum batch protocol/driver boundary; full maximum batch not simulated')
