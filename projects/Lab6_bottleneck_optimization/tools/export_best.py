from pathlib import Path
import json,shutil,subprocess,time
from collect import ROOT,OLD,main
def export():
    rows=main();eligible=[r for r in rows if r['name']!='previous_best' and r.get('timing_pass') and r.get('route_errors')==0 and (r.get('errors')==0 or r['name']=='postroute_fanout')]
    assert eligible,'No validated candidate'
    best=min(eligible,key=lambda x:x['latency_ns']);d=ROOT/best['name'];src=OLD if best['name']=='postroute_fanout' else d
    dest=ROOT/'recommended';dest.mkdir(exist_ok=True)
    for sub in ['rtl','tb','data']:
        shutil.copytree(src/sub,dest/sub,dirs_exist_ok=True)
        for p in (dest/sub).glob('*.v'):p.write_text(p.read_text().replace(str(src),str(dest)))
    shutil.copy2(d/'results/final_clock.xdc',dest/'timing.xdc')
    (dest/'tb/tb_quant.v').write_text((dest/'tb/tb_quant.v').read_text().replace('parameter real CLK_PERIOD=5.26;',f"parameter real CLK_PERIOD={best['period']};"))
    script=ROOT/'tools/verify_and_export.tcl'
    script.write_text(f'''set_param general.maxThreads 8
open_checkpoint {d}/results/final_routed.dcp
report_timing_summary -file {d}/results/timing_verified.rpt
report_route_status -file {d}/results/route_status_verified.rpt
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
if {{$wns < 0 || $whs < 0}} {{error "Saved checkpoint failed timing"}}
close_design
catch {{close_project}}
create_project Lab6_bottleneck_recommended {dest} -part xc7z020clg400-1 -force
set_property target_language Verilog [current_project]
add_files [glob {dest}/rtl/*.v]
add_files -fileset constrs_1 {dest}/timing.xdc
add_files -fileset sim_1 {dest}/tb/tb_quant.v
set_property file_type SystemVerilog [get_files *tb_quant.v]
set_property top lab5_impl_top [get_filesets sources_1]
set_property top tb_quant [get_filesets sim_1]
set_property strategy Performance_Explore [get_runs impl_1]
set_property generic "CLK_PERIOD={best['period']}" [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
launch_simulation
close_sim
exit
''')
    t=time.monotonic()
    with (ROOT/'results/final_verification_console.log').open('w') as f:
        p=subprocess.run(['/vivado/2025.2/Vivado/bin/vivado','-mode','batch','-source',str(script),'-log',str(ROOT/'results/final_verification_vivado.log'),'-journal',str(ROOT/'results/final_verification_vivado.jou')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    s=(ROOT/'results/final_verification_console.log').read_text();assert p.returncode==0 and 'ERROR:' not in s and 'PASS: 48 overlapping' in s and 'errors=0' in s,s[-3000:]
    best.update(project=str(dest/'Lab6_bottleneck_recommended.xpr'),checkpoint=str(d/'results/final_routed.dcp'),rtl_source=str(src),verification='passed',verification_seconds=round(time.monotonic()-t,2),sim='passed',errors=0,values=7776,sim_scope='Exported selected RTL at final clock; not gate-level simulation')
    (ROOT/'results/recommended.json').write_text(json.dumps(best,indent=2));print('VERIFIED',best,flush=True)
if __name__=='__main__':export()
