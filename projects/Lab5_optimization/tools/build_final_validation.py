from pathlib import Path
import sys
r=Path('/home/ding/vivado_project/Lab5_optimization');d=r/sys.argv[1]
s=(r/'rtl/tb_lab5_top.v').read_text().replace('module tb_lab5_top;','module tb_lab5_validation;')
a=s.index(' f=$fopen(');b=s.index(' repeat(5)',a);s=s[:a]+s[b:]
s=s.replace('job<3','job<6').replace('  @(negedge clk_i);n1=0;', '''  @(negedge clk_i);
  f=$fopen($sformatf("/home/ding/vivado_project/Lab5_optimization/data/validation/case%0d_fc1.txt",job),"r");for(i=0;i<128;i=i+1)scan=$fscanf(f,"%d",ref1[i]);$fclose(f);
  f=$fopen($sformatf("/home/ding/vivado_project/Lab5_optimization/data/validation/case%0d_fc2.txt",job),"r");for(i=0;i<32;i=i+1)scan=$fscanf(f,"%d",ref2[i]);$fclose(f);
  f=$fopen($sformatf("/home/ding/vivado_project/Lab5_optimization/data/validation/case%0d_fc3.txt",job),"r");for(i=0;i<2;i=i+1)scan=$fscanf(f,"%d",ref3[i]);$fclose(f);
  $readmemh($sformatf("/home/ding/vivado_project/Lab5_optimization/data/validation/input%0d.mem",job),input_bytes);
  for(gg=0;gg<dut.u_fc1.GROUPS;gg=gg+1)for(ll=0;ll<dut.u_fc1.LANES;ll=ll+1)begin
   if(gg*dut.u_fc1.LANES+ll<512) dut.u_fc1.inputs[gg][dut.u_fc1.LANES*8-1-ll*8 -:8]=input_bytes[gg*dut.u_fc1.LANES+ll];
   else dut.u_fc1.inputs[gg][dut.u_fc1.LANES*8-1-ll*8 -:8]=0;
  end
  n1=0;''')
s=s.replace('integer f,i,scan,','reg [7:0] input_bytes[0:511];\ninteger gg,ll;\ninteger f,i,scan,').replace('PASS: three consecutive networks, all 486 values and addresses match','PASS: six different consecutive networks, all 972 values and addresses match')
(d/'tb/tb_lab5_validation.v').write_text(s)
project=next((d/'vivado').glob('*.xpr'))
(d/'tools/run_final_validation.tcl').write_text(f'''open_project {project}
add_files -fileset sim_1 {d}/tb/tb_lab5_validation.v
set_property top tb_lab5_validation [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
close_sim
exit
''')
