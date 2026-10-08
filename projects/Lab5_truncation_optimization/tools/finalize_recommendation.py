#!/usr/bin/env python3
"""Reopen the selected routed DCP and create a usable project at its verified clock."""
from pathlib import Path
import json,subprocess,time
from search_quantization import ROOT
from write_report import main as write_report

def main():
    write_report();c=json.loads((ROOT/'results/recommended.json').read_text());d=ROOT/c['name'];period=c['period']
    script=ROOT/'tools/verify_and_export.tcl'
    script.write_text(f'''set_param general.maxThreads 8
open_checkpoint {d}/results/final_routed.dcp
report_timing_summary -file {d}/results/timing_verified.rpt
report_route_status -file {d}/results/route_status_verified.rpt
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
if {{$wns < 0 || $whs < 0}} {{error "Selected saved checkpoint failed timing"}}
close_design
catch {{close_project}}
create_project Lab5_truncation_recommended {ROOT}/recommended -part xc7z020clg400-1 -force
set_property target_language Verilog [current_project]
add_files [glob {d}/rtl/*.v]
add_files -fileset constrs_1 {d}/results/final_clock.xdc
add_files -fileset sim_1 {d}/tb/tb_quant.v
set_property file_type SystemVerilog [get_files *tb_quant.v]
set_property top lab5_impl_top [get_filesets sources_1]
set_property top tb_quant [get_filesets sim_1]
set_property strategy Performance_Explore [get_runs impl_1]
set_property generic "CLK_PERIOD={period}" [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
launch_simulation
close_sim
exit
''')
    started=time.monotonic()
    with (ROOT/'results/final_verification_console.log').open('w') as f:
        res=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source',str(script),
           '-log',str(ROOT/'results/final_verification_vivado.log'),'-journal',str(ROOT/'results/final_verification_vivado.jou')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    log=(ROOT/'results/final_verification_console.log').read_text(errors='replace')
    assert res.returncode==0 and 'ERROR:' not in log and 'PASS: 48 overlapping' in log and 'errors=0' in log,log[-5000:]
    state=dict(selected=c['name'],period=period,status='passed',elapsed_seconds=round(time.monotonic()-started,2),
               project=str(ROOT/'recommended/Lab5_truncation_recommended.xpr'))
    (ROOT/'results/final_verification.json').write_text(json.dumps(state,indent=2))
    print('PASS: saved routed checkpoint verified; final-clock simulation passes; recommended project exported')

if __name__=='__main__':main()
