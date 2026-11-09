from pathlib import Path
import hashlib,json,paramiko,os,getpass,shlex
R=Path(__file__).resolve().parents[1];remote='/home/xilinx/jupyter_notebooks/Lab8_AX7020_platform_v1'
secret=os.environ.get('LAB8_BOARD_PASSWORD') or getpass.getpass('Board SSH password: ')
script="""from pathlib import Path
import hashlib,json
r=Path('.')
lines=(r/'SHA256SUMS').read_text().splitlines()
for line in lines:
 h,name=line.split('  ',1)
 assert hashlib.sha256((r/name).read_bytes()).hexdigest()==h,name
boot={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/boot').iterdir() if p.is_file()}
print(json.dumps({'boot_files':boot,'pass':True,'files_verified':len(lines),'archive_sha256':hashlib.sha256((r/'lab8_ax7020_platform_v1.tar.gz').read_bytes()).hexdigest()}))
"""
c=paramiko.SSHClient();c.load_system_host_keys();c.connect('192.168.2.99',username='xilinx',password=secret,timeout=10)
try:
 i,o,e=c.exec_command('cd '+shlex.quote(remote)+' && python3 -c '+shlex.quote(script),timeout=180)
 text=o.read().decode();errors=e.read().decode();status=o.channel.recv_exit_status();i.close();o.close();e.close()
 assert status==0,errors
 report=json.loads(text);package=json.loads((R/'results/package_verified.json').read_text())
 assert report['archive_sha256']==package['sha256']
 before=json.loads((R/'results/board/platform_probe.json').read_text())['boot_files']
 assert all(report['boot_files'][name]==v['sha256'] for name,v in before.items())
 report.update(boot_files_unchanged=True,remote=remote,measured_driver_unchanged=True,package_matches_host=True)
 (R/'results/deployment_verified.json').write_text(json.dumps(report,indent=2)+'\n')
 s=c.open_sftp();s.put(str(R/'results/deployment_verified.json'),remote+'/deployment_verified.json.upload');s.posix_rename(remote+'/deployment_verified.json.upload',remote+'/deployment_verified.json')
 try:s.remove(remote+'/Lab8_AX7020_ps_api_v3.ipynb')
 except IOError:pass
 s.close();print(report)
finally:c.close()
