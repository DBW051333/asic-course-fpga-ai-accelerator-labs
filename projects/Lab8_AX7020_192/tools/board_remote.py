"""SSH/SFTP board helper; password comes from LAB8_BOARD_PASSWORD or a prompt."""
from pathlib import Path
import argparse,getpass,json,os,shlex
import paramiko
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('action',choices=['deploy','run','collect']);p.add_argument('--command');a=p.parse_args()
remote='/home/xilinx/jupyter_notebooks/Lab8_AX7020_192'
secret=os.environ.get('LAB8_BOARD_PASSWORD') or getpass.getpass('Board SSH password: ')
c=paramiko.SSHClient();c.load_system_host_keys();c.connect('192.168.2.99',username='xilinx',password=secret,timeout=10)
try:
 if a.action=='deploy':
  s=c.open_sftp()
  try:s.mkdir(remote)
  except IOError:pass
  stage=R/'deploy/lab8_ax7020_192'
  for file in sorted(stage.rglob('*')):
   destination=remote+'/'+str(file.relative_to(stage))
   if file.is_dir():
    try:s.mkdir(destination)
    except IOError:pass
   else:s.put(str(file),destination)
  s.put(str(R/'deploy/lab8_ax7020_192.tar.gz'),remote+'/lab8_ax7020_192.tar.gz')
  s.close();print('Uploaded deployment to',remote)
 elif a.action=='run':
  cmd='sudo -S -p "" bash -lc '+shlex.quote('cd '+remote+' && '+a.command)
  i,o,e=c.exec_command(cmd,timeout=900);i.write(secret+'\n');i.flush()
  output=o.read().decode();errors=e.read().decode();status=o.channel.recv_exit_status()
  d=R/'results/board';d.mkdir(parents=True,exist_ok=True)
  name='command_'+__import__('time').strftime('%Y%m%d_%H%M%S')+'.log';(d/name).write_text(output+errors+'\nEXIT '+str(status)+'\n')
  print(output);print(errors);print('EXIT',status);i.close();o.close();e.close()
  if status:raise SystemExit(status)
 else:
  s=c.open_sftp();d=R/'results/board';d.mkdir(parents=True,exist_ok=True)
  def fetch(src,dst):
   import stat
   dst.mkdir(parents=True,exist_ok=True)
   for attr in s.listdir_attr(src):
    if stat.S_ISDIR(attr.st_mode):fetch(src+'/'+attr.filename,dst/attr.filename)
    else:s.get(src+'/'+attr.filename,str(dst/attr.filename))
  for folder in ['board_acceptance','board_scalar']:
   try:fetch(remote+'/'+folder,d/folder)
   except IOError:pass
  for name in ['batch_board_results.json','api_board_results.json','environment.txt']:
   try:s.get(remote+'/'+name,str(d/name))
   except IOError:pass
  s.close();print('Collected board evidence',d)
finally:c.close()
