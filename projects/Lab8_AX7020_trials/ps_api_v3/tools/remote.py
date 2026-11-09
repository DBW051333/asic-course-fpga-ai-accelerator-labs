from pathlib import Path
import paramiko,sys,shlex,os,getpass
R=Path(__file__).resolve().parents[1];remote='/home/xilinx/jupyter_notebooks/Lab8_AX7020_ps_api_v3'
secret=os.environ.get('LAB8_BOARD_PASSWORD') or getpass.getpass('Board SSH password: ')
c=paramiko.SSHClient();c.load_system_host_keys();c.connect('192.168.2.99',username='xilinx',password=secret,timeout=10)
try:
 if sys.argv[1]=='upload':
  s=c.open_sftp()
  try:s.mkdir(remote)
  except IOError:pass
  for f in (R/'ps').iterdir():
   if f.is_file() and f.suffix in ['.py','.bin','.json','.ipynb']:
    s.put(str(f),remote+'/'+f.name+'.upload');s.posix_rename(remote+'/'+f.name+'.upload',remote+'/'+f.name)
  for name in ['lab8.bit','lab8.hwh']:
   s.put(str(R/'overlay'/name),remote+'/'+name+'.upload');s.posix_rename(remote+'/'+name+'.upload',remote+'/'+name)
  s.close();print('uploaded',remote)
 elif sys.argv[1]=='collect':
  s=c.open_sftp()
  def fetch(src,dst):
   import stat
   dst.mkdir(parents=True,exist_ok=True)
   for f in s.listdir_attr(src):
    if stat.S_ISDIR(f.st_mode):
     if f.filename in ['board_acceptance','board_scalar']:fetch(src+'/'+f.filename,dst/f.filename)
    elif f.filename.endswith(('.json','.txt','.pstats')):s.get(src+'/'+f.filename,str(dst/f.filename))
  fetch(remote,R/'results/board');s.close()
 else:
  cmd='sudo -S -p "" bash -lc '+shlex.quote('cd '+remote+' && '+sys.argv[2])
  i,o,e=c.exec_command(cmd,timeout=900);i.write(secret+'\n');i.flush()
  output=o.read().decode();err=e.read().decode();status=o.channel.recv_exit_status()
  (R/'results/board'/('command_'+__import__('time').strftime('%Y%m%d_%H%M%S')+'.log')).write_text(output+err+'\nEXIT '+str(status))
  print(output+err);i.close();o.close();e.close();sys.exit(status)
finally:c.close()
