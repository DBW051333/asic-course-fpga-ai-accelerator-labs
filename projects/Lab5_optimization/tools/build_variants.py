from pathlib import Path
import re, shutil, json
R=Path('/home/ding/vivado_project/Lab5_optimization')
D=Path('/home/ding/vivado_project/Lab5/data/params')
def values(n):
    s=(D/n).read_text().split('memory_initialization_vector')[1].split('=',1)[1]
    return [int(v,2)-(256 if v[0]=='1' else 0) for v in re.findall('[01]{8}',s)]
w1,w2,w3=[values(n) for n in ('fc1.0.weight.coe','fc2.0.weight.coe','fc3.weight.coe')]
b1,b2,b3=[values(n) for n in ('fc1.0.bias.coe','fc2.0.bias.coe','fc3.bias.coe')]
u1=[max(0,b1[o]+sum(max(-128*w,127*w) for w in w1[o*512:(o+1)*512])) for o in range(128)]
l2=[b2[o]+sum(min(0,w)*u for w,u in zip(w2[o*128:(o+1)*128],u1)) for o in range(32)]
u2=[max(0,b2[o]+sum(max(0,w)*u for w,u in zip(w2[o*128:(o+1)*128],u1))) for o in range(32)]
l3=[b3[o]+sum(min(0,w)*u for w,u in zip(w3[o*32:(o+1)*32],u2)) for o in range(2)]
u3=[b3[o]+sum(max(0,w)*u for w,u in zip(w3[o*32:(o+1)*32],u2)) for o in range(2)]
(R/'data/bounds.json').write_text(json.dumps(dict(fc1_upper=u1,fc2_lower=l2,fc2_upper=u2,fc3_lower=l3,fc3_upper=u3),indent=2))
for layer,wi,bi,ni,no in [(2,w2,b2,128,32),(3,w3,b3,32,2)]:
    (R/f'data/fc{layer}_weights.mem').write_text('\n'.join(''.join(f'{wi[o*ni+i]&255:02x}' for o in range(no)) for i in range(ni))+'\n')
    (R/f'data/fc{layer}_bias.mem').write_text('\n'.join(f'{b&255:02x}' for b in bi)+'\n')
def tree(lanes,parts):
    out=['module adder_tree(input wire clk,rst_n,input wire [%d:0] data,output wire [31:0] sum_out);'%(lanes*16-1),'wire signed [15:0] p[0:%d];'%(lanes-1),'genvar i; generate for(i=0;i<%d;i=i+1) begin:u assign p[i]=data[%d-i*16 -:16]; end endgenerate'%(lanes,lanes*16-1)]
    count,width,prev=lanes,16,'p'
    for st,nlevels in enumerate(parts):
        for lev in range(nlevels):
            count//=2; name=f'w{st}_{lev}';out.append(f'wire signed [{width}:0] {name}[0:{count-1}];')
            out.append(f'generate for(i=0;i<{count};i=i+1) begin:a{st}_{lev} assign {name}[i]={{ {prev}[2*i][{width-1}],{prev}[2*i] }} + {{ {prev}[2*i+1][{width-1}],{prev}[2*i+1] }}; end endgenerate')
            width+=1;prev=name
        reg=f's{st}';out.append(f'reg signed [{width-1}:0] {reg}[0:{count-1}]; integer k{st}; always @(posedge clk) begin for(k{st}=0;k{st}<{count};k{st}=k{st}+1) {reg}[k{st}] <= {prev}[k{st}]; end');prev=reg
    assert count==1
    out.append(f'assign sum_out={{{{{32-width}{{{prev}[0][{width-1}]}}}},{prev}[0]}}; endmodule')
    return '\n'.join(out)+'\n'
for name,source,exact,parts in [('stream128_full','Lab4_optimized',False,None),('stream128_exact','Lab4_optimized',True,None),('stream128_tree4','Lab4_optimized',True,[2,2,2,1]),('stream128_tree1222','Lab4_optimized',True,[1,2,2,2]),('stream64_tree1221','Lab4_tree4_1221_full4p3',True,None)]:
    root=R/name
    for sub in ('rtl','tools','tb','results'): (root/sub).mkdir(parents=True,exist_ok=True)
    src=Path('/home/ding/vivado_project')/source
    for f in ('fc.v','fc_top.v','mult_array.v'): shutil.copy2(src/f,root/'rtl'/f)
    shutil.copy2(src/'Lab4.srcs/sources_1/new/adder_tree.v',root/'rtl/adder_tree.v')
    shutil.copy2(R/'rtl/fc_stream.v',root/'rtl/fc_stream.v')
    if parts:
        (root/'rtl/adder_tree.v').write_text(tree(128,parts))
        p=root/'rtl/fc.v';s=p.read_text()
        s=s.replace('group_idx_dly[12]','group_idx_dly[13]').replace('out_channel_dly[12]','out_channel_dly[13]').replace('group_idx_dly[10]','group_idx_dly[11]').replace('group_idx_dly[9]','group_idx_dly[10]')
        s=s.replace('bias_reg [0:8]','bias_reg [0:9]').replace('i<=8','i<=9').replace('i <= 8','i <= 9').replace('bias_reg[8]','bias_reg[9]');p.write_text(s)
    iw2,aw2,iw3,aw3=(23,35,35,45) if exact else (32,48,48,64)
    top='''module lab5_top(input wire clk_i,rst_n_i,start_i,output wire done_o,output wire fc1_wren_o,output wire [31:0] fc1_data_o,output wire [6:0] fc1_addr_o,output wire fc2_wren_o,output wire [47:0] fc2_data_o,output wire [4:0] fc2_addr_o,output wire fc3_wren_o,output wire [63:0] fc3_data_o,output wire fc3_addr_o);
wire d1,d2;
fc_top u_fc1(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.done_o(d1),.fc_output_wren_o(fc1_wren_o),.fc_output_data_o(fc1_data_o),.fc_output_addr_o(fc1_addr_o));
'''
    for layer,iw,aw,ow,ni,no,ia,oa,relu in [(2,iw2,aw2,48,128,32,7,5,1),(3,iw3,aw3,64,32,2,5,1,0)]:
        pre=layer-1
        top+=f'''fc_stream #(.IW({iw}),.NI({ni}),.NO({no}),.AW({aw}),.OW({ow}),.IA({ia}),.OA({oa}),.RELU({relu}),.WEIGHT_FILE("{R}/data/fc{layer}_weights.mem"),.BIAS_FILE("{R}/data/fc{layer}_bias.mem")) u_fc{layer}(.clk_i(clk_i),.rst_n_i(rst_n_i),.valid_i(fc{pre}_wren_o),.data_i(fc{pre}_data_o[{iw-1}:0]),.addr_i(fc{pre}_addr_o),.valid_o(fc{layer}_wren_o),.data_o(fc{layer}_data_o),.addr_o(fc{layer}_addr_o),.done_o({'d2' if layer==2 else 'done_o'}));\n'''
    (root/'rtl/lab5_top.v').write_text(top+'endmodule\n')
    ips=[src/f'Lab4.srcs/sources_1/ip/{n}/{n}.xci' for n in ('fc_input_ram','fc_weight_ram','fc_bias_ram','fc_output_ram','mult_8')]
    create=f'''create_project {name} {root}/vivado -part xc7z020clg400-1 -force
set_property target_language Verilog [current_project]
add_files [list {' '.join(str(p) for p in ips)}]
add_files [glob {root}/rtl/*.v]
add_files -fileset sim_1 {root}/tb/tb_lab5_top.v
set_property top lab5_top [get_filesets sources_1]
set_property top tb_lab5_top [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
set fh [open {root}/timing.xdc w]; puts $fh {{create_clock -period 10.000 [get_ports clk_i]}}; close $fh
add_files -fileset constrs_1 {root}/timing.xdc
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
launch_simulation
close_sim
exit
'''
    (root/'tools/create_sim.tcl').write_text(create)
    run=f'''open_project {root}/vivado/{name}.xpr
launch_runs synth_1 -jobs 2
wait_on_run synth_1
open_run synth_1
report_utilization -hierarchical -file {root}/results/utilization_hier_synth.rpt
report_utilization -file {root}/results/utilization_synth.rpt
report_timing_summary -file {root}/results/timing_synth.rpt
close_design
launch_runs impl_1 -to_step route_design -jobs 2
wait_on_run impl_1
open_run impl_1
report_utilization -file {root}/results/utilization_impl.rpt
report_timing_summary -file {root}/results/timing_impl.rpt
exit
'''
    (root/'tools/run_impl.tcl').write_text(run)
    shutil.copy2(R/'rtl/tb_lab5_top.v',root/'tb/tb_lab5_top.v')
    print(name)
