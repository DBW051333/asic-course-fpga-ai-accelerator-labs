from pathlib import Path
import shutil
r=Path('/home/ding/vivado_project/Lab5_optimization');src=r/'stream_pair256_burst_exact23_tree7_clk4p8';d=r/'stream_pair256_banked_exact23_tree7_clk4p8'
for n in ['rtl','tb','tools']:shutil.copytree(src/n,d/n,dirs_exist_ok=True)
(d/'results').mkdir(exist_ok=True)
rows=(r/'data/stream_pair256_hybrid_weights.mem').read_text().split()
for b in range(8):(r/f'data/fc1_bank{b}.mem').write_text('\n'.join(line[b*128:(b+1)*128] for line in rows)+'\n')
p=d/'rtl/fc1_paired.v';s=p.read_text().replace(' (* rom_style="block" *) reg [LANES*16-1:0] weights[0:64*GROUPS-1];','')
s=s.replace('$readmemh(WEIGHTS,weights);','').replace('reg [LANES*16-1:0] weight_r;reg [LANES*8-1:0] input_r;','wire [LANES*16-1:0] weight_r;reg [LANES*8-1:0] input_r,input_rd;')
s=s.replace('reg [13:0] valid_pipe;reg [7:0] tag[0:13]','reg [14:0] valid_pipe;reg [7:0] tag[0:14]').replace('tag[13]','tag[14]').replace('valid_pipe[12:0]','valid_pipe[13:0]').replace('j<14','j<15').replace('valid_pipe[13])','valid_pipe[14])')
s=s.replace('weight_r<=weights[issue_addr];input_r<=inputs[issue_group];','input_r<=inputs[issue_group];input_rd<=input_r;').replace('input_p[j]<=input_r[','input_p[j]<=input_rd[')
files=[str(r/f'data/fc1_bank{b}.mem') for b in range(8)]
select=' : '.join(f'(bank=={b})?"{files[b]}"' for b in range(7))+' : "'+files[7]+'"'
banks=''' genvar bank;generate for(bank=0;bank<8;bank=bank+1)begin:weight_bank
  localparam BANK_WIDTH=LANES*16/8;
  localparam BANK_FILE='''+select+''';
  (* rom_style="block" *) reg [BANK_WIDTH-1:0] weights_b[0:64*GROUPS-1];
  (* keep="true",dont_touch="true" *) reg [6:0] local_addr;
  reg [BANK_WIDTH-1:0] local_weight;
  initial $readmemh(BANK_FILE,weights_b);
  always @(posedge clk_i)begin
   if(!rst_n_i)local_addr<=0;else local_addr<=issue_addr[6:0];
   local_weight<=weights_b[local_addr];
  end
  assign weight_r[LANES*16-1-bank*BANK_WIDTH -:BANK_WIDTH]=local_weight;
 end endgenerate
'''
s=s.replace(' integer j;',banks+' integer j;');p.write_text(s)
for p in (d/'tools').glob('*.tcl'):
 s=p.read_text().replace(str(src),str(d)).replace(src.name+'.xpr',d.name+'.xpr').replace('create_project '+src.name,'create_project '+d.name);p.write_text(s)
print(d)
