from pathlib import Path
import shutil
r=Path('/home/ding/vivado_project/Lab5_optimization')
s=(r/'rtl/fc_stream.v').read_text().replace('(* rom_style="block" *)','localparam ROM_STYLE=(NO==2)?"distributed":"block";\n    (* rom_style=ROM_STYLE *)')
s=s.replace('reg signed [IW-1:0] data_r;','reg signed [IW-1:0] data_r,data_d;\n    reg [NO*8-1:0] weight_d;')
s=s.replace('reg [2:0] valid_pipe, first_pipe, last_pipe;','reg [3:0] valid_pipe, first_pipe, last_pipe;')
s=s.replace('data_r <= data_i;','data_r <= data_i;\n        data_d <= data_r; weight_d <= weight_r;')
s=s.replace('data_r * $signed(weight_r[','data_d * $signed(weight_d[')
s=s.replace('valid_pipe[1:0]','valid_pipe[2:0]').replace('first_pipe[1:0]','first_pipe[2:0]').replace('last_pipe[1:0]','last_pipe[2:0]')
s=s.replace('valid_pipe[2])','valid_pipe[3])').replace('first_pipe[2])','first_pipe[3])').replace('last_pipe[2])','last_pipe[3])')
(r/'rtl/fc_stream_staged.v').write_text(s)
for old,new in [('stream_pair128','stream_pair128_staged'),('stream_pair171','stream_pair171_staged'),('stream_pair256_hybrid','stream_pair256_staged')]:
 src=r/old;dst=r/new
 for folder in ('rtl','tb','tools'):shutil.copytree(src/folder,dst/folder,dirs_exist_ok=True)
 (dst/'results').mkdir(exist_ok=True)
 (dst/'rtl/fc_stream.v').write_text(s)
 for p in (dst/'tools').glob('*.tcl'):p.write_text(p.read_text().replace(str(src),str(dst)).replace('create_project '+old,'create_project '+new).replace('/vivado/'+old+'.xpr','/vivado/'+new+'.xpr'))
 print(new)
