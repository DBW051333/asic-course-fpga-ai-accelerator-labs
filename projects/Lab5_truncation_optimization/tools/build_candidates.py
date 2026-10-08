#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, shutil,sys
import numpy as np
from search_quantization import ROOT,BASE,X,W,B,LABELS,infer

QUANT_RTL = '''// One quantization per completed layer. Nearest rounding ties toward +infinity.
module quantize_signed #(parameter IW=23,OW=8,SHIFT=10,ROUND=0,SAT=0)(
 input wire signed [IW-1:0] data_i,output wire signed [OW-1:0] data_o);
 localparam signed [IW:0] HALF=(SHIFT>0)?({{IW{1'b0}},1'b1} << (SHIFT-1)):0;
 localparam signed [IW:0] HIGH=({{IW{1'b0}},1'b1} << (OW-1))-1;
 localparam signed [IW:0] LOW=-({{IW{1'b0}},1'b1} << (OW-1));
 wire signed [IW:0] extended={data_i[IW-1],data_i};
 wire signed [IW:0] shifted=(extended+(ROUND?HALF:0)) >>> SHIFT;
 assign data_o=SAT?((shifted>HIGH)?HIGH[OW-1:0]:((shifted<LOW)?LOW[OW-1:0]:shifted[OW-1:0])):shifted[OW-1:0];
endmodule
'''

def modify_tail(path,kind,layer):
    s=path.read_text()
    if kind=='lut':s=s.replace('use_dsp="yes"','use_dsp="no"')
    if kind in ('packed','packed_rom'):
        assert layer in (2,3)
        n='NO-1' if layer==2 else 'NO*4-1'
        s=s.replace(f'(* use_dsp="yes" *) reg signed [PW-1:0] product [0:{n}];',
                    f'wire signed [PW-1:0] product [0:{n}];')
        if layer==2:
            assign='''
    localparam PPW=IW+25;
    genvar g;generate for(g=0;g<NO/2;g=g+1)begin:packed_mult
      wire signed [7:0] w0=weight_d[NO*8-1-2*g*8 -:8];
      wire signed [7:0] w1=weight_d[NO*8-9-2*g*8 -:8];
      wire signed [24:0] packed_w={w1[7],w1,16'd0}+{{17{w0[7]}},w0};
      (* use_dsp="yes" *) reg signed [PPW-1:0] packed_p;
      always @(posedge clk_i)packed_p<=packed_w*data_d;
      wire signed [15:0] high_product=$signed(packed_p[PPW-1:16])+{15'd0,packed_p[15]};
      assign product[2*g]=packed_p[PW-1:0];
      assign product[2*g+1]=high_product[PW-1:0];
    end endgenerate
'''
            s=s.replace('    integer j;',assign+'    integer j;')
            s=s.replace('            product[j] <= data_d * $signed(weight_d[NO*8-1-j*8 -:8]);\n','')
        else:
            assign='''
    // Two output channels share each of the four activation lanes.
    localparam PPW=IW+25;
    genvar g;generate for(g=0;g<4;g=g+1)begin:packed_mult
      wire signed [7:0] w0=weight_d[NO*32-1-g*8 -:8];
      wire signed [7:0] w1=weight_d[NO*32-33-g*8 -:8];
      wire signed [IW-1:0] x=(g==0)?data_d:((g==1)?data_b_d:((g==2)?data_c_d:data_d_d));
      wire signed [24:0] packed_w={w1[7],w1,16'd0}+{{17{w0[7]}},w0};
      (* use_dsp="yes" *) reg signed [PPW-1:0] packed_p;
      always @(posedge clk_i)packed_p<=packed_w*x;
      wire signed [15:0] high_product=$signed(packed_p[PPW-1:16])+{15'd0,packed_p[15]};
      assign product[g]=packed_p[PW-1:0];
      assign product[4+g]=high_product[PW-1:0];
    end endgenerate
'''
            s=s.replace('    integer j;',assign+'    integer j;')
            for line in s.splitlines():
                if 'product[j*4' in line and '<=' in line and '*' in line.split('<=')[1] and 'weight_d' in line:
                    s=s.replace(line+'\n','')
        if kind=='packed_rom':
            rw='(NO/2)*25' if layer==2 else '4*25'
            s=s.replace('    localparam PW=IW+8;',f'    localparam PW=IW+8;\n    localparam RW={rw};')
            s=s.replace('NO*8-1:0','RW-1:0') if layer==2 else s.replace('NO*32-1:0','RW-1:0')
            lines=s.splitlines()
            lines=[line for line in lines if not ('wire signed [7:0] w0=' in line or 'wire signed [7:0] w1=' in line)]
            lines=[('      wire signed [24:0] packed_w=weight_d[RW-1-g*25 -:25];' if 'wire signed [24:0] packed_w=' in line else line) for line in lines]
            s='\n'.join(lines)+'\n'
    path.write_text(s)

def top(c):
    w1,w2,w3=c['widths'];s1,s2,s3=c['shifts'];rounding=int(c['mode']=='round_sat');sat=int(c['mode']!='floor_wrap')
    aw2=w1+15;aw3=w2+13
    data=ROOT.parent/'Lab5_optimization/data'
    weight2=ROOT/c['name']/'data/fc2_packed_weights.mem' if c['tail']=='packed_rom' else data/'fc2_weights.mem'
    weight3=ROOT/c['name']/'data/fc3_packed_weights.mem' if c['tail']=='packed_rom' else data/'fc3_quad_weights.mem'
    return f'''module lab5_top(input wire clk_i,rst_n_i,start_i,output wire done_o,ready_o,
 output wire fc1_wren_o,output wire [{w1-1}:0] fc1_data_o,output wire [6:0] fc1_addr_o,
 output wire fc2_wren_o,output wire [{w2-1}:0] fc2_data_o,fc2_data_b_o,fc2_data_c_o,fc2_data_d_o,output wire [4:0] fc2_addr_o,
 output wire fc3_wren_o,output wire [{w3-1}:0] fc3_data_o,output wire fc3_addr_o);
 wire d1,d2;wire [31:0] full1;wire [{aw2-1}:0] full2,full2b,full2c,full2d;wire [{aw3-1}:0] full3;
 fc1_paired #(.LANES(256),.GROUPS(2),.ADDER_LANES(256),.DSP_LANES({c['dsp1']}),
 .WEIGHTS("{data}/stream_pair256_hybrid_weights.mem"),.INPUTS("{data}/stream_pair256_hybrid_inputs.mem"),.BIASES("{data}/fc1_paired_bias.mem"))
 u_fc1(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.done_o(d1),.ready_o(ready_o),.fc_output_wren_o(fc1_wren_o),.fc_output_data_o(full1),.fc_output_addr_o(fc1_addr_o));
 quantize_signed #(.IW(32),.OW({w1}),.SHIFT({s1}),.ROUND({rounding}),.SAT({sat})) q1(.data_i(full1),.data_o(fc1_data_o));
 fc_stream_pair_output #(.IW({w1}),.NI(128),.NO(32),.AW({aw2}),.OW({aw2}),.IA(7),.OA(5),.RELU(1),
 .WEIGHT_FILE("{weight2}"),.BIAS_FILE("{data}/fc2_bias.mem"))
 u_fc2(.clk_i(clk_i),.rst_n_i(rst_n_i),.valid_i(fc1_wren_o),.data_i(fc1_data_o),.addr_i(fc1_addr_o),.valid_o(fc2_wren_o),
 .data_o(full2),.data_b_o(full2b),.data_c_o(full2c),.data_d_o(full2d),.addr_o(fc2_addr_o),.done_o(d2));
 quantize_signed #(.IW({aw2}),.OW({w2}),.SHIFT({s2}),.ROUND({rounding}),.SAT({sat})) q2(.data_i(full2),.data_o(fc2_data_o));
 quantize_signed #(.IW({aw2}),.OW({w2}),.SHIFT({s2}),.ROUND({rounding}),.SAT({sat})) q2b(.data_i(full2b),.data_o(fc2_data_b_o));
 quantize_signed #(.IW({aw2}),.OW({w2}),.SHIFT({s2}),.ROUND({rounding}),.SAT({sat})) q2c(.data_i(full2c),.data_o(fc2_data_c_o));
 quantize_signed #(.IW({aw2}),.OW({w2}),.SHIFT({s2}),.ROUND({rounding}),.SAT({sat})) q2d(.data_i(full2d),.data_o(fc2_data_d_o));
 fc_stream_two_inputs #(.IW({w2}),.NI(8),.NO(2),.AW({aw3}),.OW({aw3}),.IA(3),.OA(1),.RELU(0),
 .WEIGHT_FILE("{weight3}"),.BIAS_FILE("{data}/fc3_bias.mem"))
 u_fc3(.clk_i(clk_i),.rst_n_i(rst_n_i),.valid_i(fc2_wren_o),.data_i(fc2_data_o),.data_b_i(fc2_data_b_o),.data_c_i(fc2_data_c_o),.data_d_i(fc2_data_d_o),
 .addr_i(fc2_addr_o[4:2]),.valid_o(fc3_wren_o),.data_o(full3),.addr_o(fc3_addr_o),.done_o(done_o));
 quantize_signed #(.IW({aw3}),.OW({w3}),.SHIFT({s3}),.ROUND({rounding}),.SAT({sat})) q3(.data_i(full3),.data_o(fc3_data_o));
 endmodule
'''

def testbench(c,d):
    w1,w2,w3=c['widths']
    return f'''`timescale 1ns/1ps
module tb_quant;
 parameter real CLK_PERIOD=5.26;
 reg clk_i=0,rst_n_i=0,start_i=0;always #(CLK_PERIOD/2)clk_i=~clk_i;
 wire ready_o,done_o,v1,v2,v3;wire [{w1-1}:0] d1;wire [{w2-1}:0] d2,d2b,d2c,d2d;wire [{w3-1}:0] d3;wire [6:0] a1;wire [4:0] a2;wire a3;
 wire signed [63:0] e1=$signed(d1),e2=$signed(d2),e2b=$signed(d2b),e2c=$signed(d2c),e2d=$signed(d2d),e3=$signed(d3);
 lab5_top dut(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.ready_o(ready_o),.done_o(done_o),
 .fc1_wren_o(v1),.fc1_data_o(d1),.fc1_addr_o(a1),.fc2_wren_o(v2),.fc2_data_o(d2),.fc2_data_b_o(d2b),.fc2_data_c_o(d2c),.fc2_data_d_o(d2d),.fc2_addr_o(a2),
 .fc3_wren_o(v3),.fc3_data_o(d3),.fc3_addr_o(a3));
 reg signed [63:0] ref1[0:6143],ref2[0:1535],ref3[0:95];reg [7:0] input_bytes[0:24575];reg [0:0] labels[0:41];
 integer job,gg,ll,i,errors=0,n1=0,n2=0,n3=0,completed=0,correct=0,ties=0,fd,pred;
 realtime launched[0:47],last_launch=0;integer min_latency=99999,max_latency=0,min_interval=99999,max_interval=0,cycles,interval;
 reg signed [63:0] score0;
 initial begin
  $readmemh("{d}/data/fc1_expected.mem",ref1);$readmemh("{d}/data/fc2_expected.mem",ref2);$readmemh("{d}/data/fc3_expected.mem",ref3);
  $readmemh("{ROOT}/data/all_inputs.mem",input_bytes);$readmemh("{ROOT}/data/labels.mem",labels);
  fd=$fopen("{d}/results/rtl_samples.csv","w");$fdisplay(fd,"sample,score0,score1,prediction,label,correct");
  repeat(5)@(negedge clk_i);rst_n_i=1;
  for(job=0;job<48;job=job+1)begin
   wait(ready_o);@(negedge clk_i);
   for(gg=0;gg<2;gg=gg+1)for(ll=0;ll<256;ll=ll+1) dut.u_fc1.inputs[gg][2047-ll*8 -:8]=input_bytes[job*512+gg*256+ll];
   start_i=1;launched[job]=$realtime+CLK_PERIOD/2;
   if(job>0)begin interval=$rtoi((launched[job]-last_launch)/CLK_PERIOD+0.5);if(interval<min_interval)min_interval=interval;if(interval>max_interval)max_interval=interval;end
   last_launch=launched[job];@(negedge clk_i);start_i=0;
  end
  wait(completed==48);repeat(3)@(negedge clk_i);
  if(n1!=6144 || n2!=1536 || n3!=96)begin errors=errors+1;$display("COUNT_FAIL %0d %0d %0d",n1,n2,n3);end
  $fclose(fd);
  $display("SUMMARY correct=%0d/42 ties=%0d errors=%0d values=%0d latency_cycles=%0d..%0d interval_cycles=%0d..%0d",correct,ties,errors,n1+n2+n3,min_latency,max_latency,min_interval,max_interval);
  if(errors==0)$display("PASS: 48 overlapping requests, 7776 layer outputs and addresses match");else $fatal(1,"FAIL errors=%0d",errors);
  $finish;
 end
 always @(posedge done_o)begin
  cycles=$rtoi(($realtime-launched[completed])/CLK_PERIOD+0.5);
  if(cycles<min_latency)min_latency=cycles;if(cycles>max_latency)max_latency=cycles;
  completed=completed+1;
 end
 always @(posedge clk_i)begin
  if(rst_n_i && v1)begin
   if(a1!==(n1%128) || e1!==ref1[n1])begin errors=errors+1;if(errors<10)$display("MISMATCH FC1[%0d] got=%0d expected=%0d addr=%0d",n1,e1,ref1[n1],a1);end n1=n1+1;
  end
  if(rst_n_i && v2)begin
   if(a2!==(n2%32) || e2!==ref2[n2] || e2b!==ref2[n2+1] || e2c!==ref2[n2+2] || e2d!==ref2[n2+3])begin errors=errors+1;if(errors<10)$display("MISMATCH FC2[%0d] got=%0d expected=%0d addr=%0d",n2,e2,ref2[n2],a2);end n2=n2+4;
  end
  if(rst_n_i && v3)begin
   if(a3!==(n3%2) || e3!==ref3[n3])begin errors=errors+1;if(errors<10)$display("MISMATCH FC3[%0d] got=%0d expected=%0d",n3,e3,ref3[n3]);end
   if(n3%2==0)score0=e3;
   else if(n3/2<42)begin
    pred=(score0<e3);if(pred==labels[n3/2])correct=correct+1;if(score0==e3)ties=ties+1;
    $fdisplay(fd,"%0d,%0d,%0d,%0d,%0d,%0d",n3/2,score0,e3,pred,labels[n3/2],pred==labels[n3/2]);
   end n3=n3+1;
  end
 end
 initial begin #2000000;$fatal(1,"FAIL TIMEOUT");end
endmodule
'''

def main():
    candidates=json.loads((ROOT/'results/candidates.json').read_text());(ROOT/'data').mkdir(exist_ok=True)
    extras=[]
    for i in range(6):
        extras.append(np.array([int(v,16)-(256 if int(v,16)>=128 else 0) for v in
             (ROOT.parent/f'Lab5_optimization/data/validation/input{i}.mem').read_text().split()],dtype=np.int64))
    allx=np.concatenate([X,np.array(extras)])
    (ROOT/'data/all_inputs.mem').write_text(''.join(f'{int(v)&255:02x}\n' for v in allx.flat))
    (ROOT/'data/labels.mem').write_text(''.join(f'{v}\n' for v in LABELS))
    manifest={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE/'rtl').glob('*.v')}
    (ROOT/'results/baseline_source_sha256.json').write_text(json.dumps(manifest,indent=2))
    for c in candidates:
        if len(sys.argv)>1 and c['name'] not in sys.argv[1:]:continue
        d=ROOT/c['name']
        for n in ['rtl','tb','tools','data','results']:(d/n).mkdir(parents=True,exist_ok=True)
        for name in ['fc1_paired.v','adder_tree.v','fc_stream_pair_output.v','fc_stream_two_inputs.v']:shutil.copy2(BASE/'rtl'/name,d/'rtl'/name)
        modify_tail(d/'rtl/fc_stream_pair_output.v',c['tail'],2)
        modify_tail(d/'rtl/fc_stream_two_inputs.v',c['tail'],3)
        (d/'rtl/quantize_signed.v').write_text(QUANT_RTL)
        (d/'rtl/lab5_top.v').write_text(top(c))
        if c['tail']=='packed_rom':
            words2=[];words3=[]
            for i in range(128):
                word=0
                for g in range(16):word=(word<<25)|(((int(W[1][i,2*g+1])<<16)+int(W[1][i,2*g]))&((1<<25)-1))
                words2.append(f'{word:0100x}')
            for i in range(8):
                word=0
                for g in range(4):word=(word<<25)|(((int(W[2][i*4+g,1])<<16)+int(W[2][i*4+g,0]))&((1<<25)-1))
                words3.append(f'{word:025x}')
            (d/'data/fc2_packed_weights.mem').write_text('\n'.join(words2)+'\n')
            (d/'data/fc3_packed_weights.mem').write_text('\n'.join(words3)+'\n')
        w1,w2,w3=c['widths']
        (d/'rtl/lab5_impl_top.v').write_text(f'''module lab5_impl_top(input wire clk_i,rst_n_i,start_i,output wire done_o,ready_o,result_valid_o,result_addr_o,output wire [63:0] result_data_o);
 wire v1,v2;wire [{w1-1}:0] d1;wire [{w2-1}:0] d2,d2b,d2c,d2d;wire [{w3-1}:0] d3;wire [6:0] a1;wire [4:0] a2;
 assign result_data_o={{{{{64-w3}{{d3[{w3-1}]}}}},d3}};
 lab5_top network(.clk_i(clk_i),.rst_n_i(rst_n_i),.start_i(start_i),.ready_o(ready_o),.done_o(done_o),.fc1_wren_o(v1),.fc1_data_o(d1),.fc1_addr_o(a1),
 .fc2_wren_o(v2),.fc2_data_o(d2),.fc2_data_b_o(d2b),.fc2_data_c_o(d2c),.fc2_data_d_o(d2d),.fc2_addr_o(a2),.fc3_wren_o(result_valid_o),.fc3_data_o(d3),.fc3_addr_o(result_addr_o));endmodule
''')
        layers,ranges,counts=infer(allx,c['widths'],c['shifts'],c['mode'],c.get('product_cut',0))
        if c.get('product_cut',0) or c.get('tree_stages')==8:
            k=c.get('product_cut',0)
            pre=c.get('product_cut_stage')=='register'
            if pre:
                p=d/'rtl/fc1_paired.v';s=p.read_text()
                fn=f'''function [15:0] round_product;
 input signed [16:0] value;reg signed [16:0] rounded;
 begin rounded=value+17'sd{1<<(k-1)};round_product={{rounded[15:{k}],{k}'d0}};end
 endfunction
'''
                s=s.replace(' integer j;',fn+' integer j;')
                s=s.replace('low_product[j]<=product_r[j][15:0];','low_product[j]<=round_product($signed(product_r[j][15:0]));')
                s=s.replace('high_product[j]<=$signed(product_r[j][32:16])+{16\'d0,product_r[j][15]};else high_product[j]<=product_r[j][31:16];',
                 'high_product[j]<=round_product($signed(product_r[j][32:16])+{16\'d0,product_r[j][15]});else high_product[j]<=round_product($signed(product_r[j][31:16]));')
                p.write_text(s)
            if c.get('tree_stages')==8:
                p=d/'rtl/fc1_paired.v';s=p.read_text()
                s=s.replace('reg [13:0] valid_pipe','reg [14:0] valid_pipe').replace('tag[0:13]','tag[0:14]')
                s=s.replace('tag[13]','tag[14]').replace('valid_pipe[13]','valid_pipe[14]')
                s=s.replace('valid_pipe[12:0]','valid_pipe[13:0]').replace('j<14','j<15')
                p.write_text(s)
            tree='module adder_tree(input wire clk,rst_n,input wire [4095:0] data,output wire [31:0] sum_out);\n'
            tree+=f'wire signed [{15-k}:0] p[0:255];genvar i;generate for(i=0;i<256;i=i+1)begin:cut_product\n'
            half=0 if (pre or not k) else 1<<(k-1)
            tree+=f'wire signed [16:0] rounded=$signed(data[4095-i*16 -:16])+17\'sd{half};assign p[i]=rounded[15:{k}];end endgenerate\n'
            prev='p';pw=16-k
            for level in range(8):
                n=128>>level;ow=pw+1;name=f'w{level}'
                tree+=f'wire signed [{ow-1}:0] {name}[0:{n-1}];generate for(i=0;i<{n};i=i+1)begin:a{level} assign {name}[i]={{ {prev}[2*i][{pw-1}],{prev}[2*i] }} + {{ {prev}[2*i+1][{pw-1}],{prev}[2*i+1] }};end endgenerate\n'
                if level>=1 or c.get('tree_stages')==8:
                    regname=f's{level}'
                    tree+=f'reg signed [{ow-1}:0] {regname}[0:{n-1}];integer j{level};always @(posedge clk)for(j{level}=0;j{level}<{n};j{level}=j{level}+1){regname}[j{level}]<={name}[j{level}];\n'
                    prev=regname
                else:prev=name
                pw=ow
            if k:tree+=f'assign sum_out={{{{8{{s7[0][{23-k}]}}}},s7[0],{k}\'d0}};endmodule\n'
            else:tree+='assign sum_out={{8{s7[0][23]}},s7[0]};endmodule\n'
            (d/'rtl/adder_tree.v').write_text(tree)
        c['stress_overflow_counts']=counts
        for k,a in enumerate(layers,1):
            (d/f'data/fc{k}_expected.mem').write_text(''.join(f'{int(v)&((1<<64)-1):016x}\n' for v in a.flat))
        (d/'config.json').write_text(json.dumps(c,indent=2))
        (d/'tb/tb_quant.v').write_text(testbench(c,d))
        (d/'timing.xdc').write_text('create_clock -period 4.800 [get_ports clk_i]\n')
        (d/'tools/run_sim.tcl').write_text(f'''set_param general.maxThreads 8
 create_project validation {d}/simulation -part xc7z020clg400-1 -force
 add_files [glob {d}/rtl/*.v]
 add_files -fileset sim_1 {d}/tb/tb_quant.v
 set_property top lab5_top [get_filesets sources_1]
 set_property file_type SystemVerilog [get_files *tb_quant.v]
 set_property top tb_quant [get_filesets sim_1]
 set_property xsim.simulate.runtime all [get_filesets sim_1]
 update_compile_order -fileset sources_1
 launch_simulation
 close_sim
 exit
''')
        # Non-project flow avoids an extra parent Vivado process. Save each physical stage.
        synth_threads=8 if c['name'] in ('q8_lab6_d168','q8_lab6_pack_d200') else 4
        (d/'tools/run_synth.tcl').write_text(f'''set_param general.maxThreads {synth_threads}
 create_project {c['name']} {d}/vivado -part xc7z020clg400-1 -force
 set_property target_language Verilog [current_project]
 add_files [glob {d}/rtl/*.v]
 add_files -fileset constrs_1 {d}/timing.xdc
 set_property top lab5_impl_top [get_filesets sources_1]
 update_compile_order -fileset sources_1
 synth_design -top lab5_impl_top -part xc7z020clg400-1
 write_checkpoint -force {d}/results/synth.dcp
 report_utilization -file {d}/results/utilization_synth.rpt
 report_utilization -hierarchical -file {d}/results/utilization_hier_synth.rpt
 report_timing_summary -file {d}/results/timing_synth.rpt
 exit
''')
        (d/'tools/run_impl.tcl').write_text(f'''set_param general.maxThreads 8
 open_checkpoint {d}/results/synth.dcp
 opt_design
 place_design -directive Explore
 phys_opt_design -directive Explore
 route_design -directive Explore
 report_utilization -file {d}/results/utilization_impl.rpt
 report_timing_summary -file {d}/results/timing_route_target.rpt
 report_route_status -file {d}/results/route_status.rpt
 report_drc -file {d}/results/drc.rpt
 report_timing -max_paths 10 -file {d}/results/critical_paths.rpt
 set orig [get_property PERIOD [get_clocks -of_objects [get_ports clk_i]]]
 set slack [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
 set chosen [expr {{ceil(($orig-$slack)*100.0)/100.0}}]
 create_clock -period $chosen [get_ports clk_i]
 set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
 while {{$wns<0}} {{set chosen [expr {{$chosen+0.01}}];create_clock -period $chosen [get_ports clk_i];set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]}}
 set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
 report_timing_summary -file {d}/results/timing_final.rpt
 write_checkpoint -force {d}/results/final_routed.dcp
 set fh [open {d}/results/final_clock.xdc w];puts $fh "create_clock -period $chosen \\[get_ports clk_i\\]";close $fh
 set fh [open {d}/results/final_clock.json w]
 puts $fh [format {{{{"period": %.3f, "wns": %.3f, "whs": %.3f, "route_target": %.3f}}}} $chosen $wns $whs $orig];close $fh
 create_clock -period [expr {{$chosen-0.01}}] [get_ports clk_i]
 report_timing_summary -file {d}/results/timing_boundary.rpt
 exit
''')
        print('built',d.name)
    (ROOT/'results/candidates.json').write_text(json.dumps(candidates,indent=2))

if __name__=='__main__':main()
