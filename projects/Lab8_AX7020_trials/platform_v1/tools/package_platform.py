from pathlib import Path
import hashlib,json,shutil,tarfile
R=Path(__file__).resolve().parents[1];stage=R/'deploy/lab8_ax7020_platform_v1';stage.mkdir(parents=True,exist_ok=True)
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
for f in (R/'ps').iterdir():
 if f.is_file() and f.suffix in ('.py','.bin','.json','.ipynb','.bit','.hwh'):shutil.copy2(f,stage/f.name)
for name in ['lab8.bit','lab8.hwh']:shutil.copy2(R/'overlay'/name,stage/name)
shutil.copy2(R/'overlay/lab8.xsa',stage/'lab8_ax7020_platform_v1.xsa')
for name in ['README.md','experiment.json']:shutil.copy2(R/name,stage/name)
for name in ['optimization_summary.json','optimization_report.md','driver.diff','checkpoint_verified.json','dsp_audit.json','python_tests.json','simulation_axis.json','simulation_dma.json']:shutil.copy2(R/'results'/name,stage/name)
shutil.copytree(R/'results/board',stage/'board_evidence',dirs_exist_ok=True)
shutil.copytree(R/'evidence',stage/'provenance',dirs_exist_ok=True)
(stage/'cpu_767_offline_only').mkdir(exist_ok=True)
for name in ['cpu_767.xsa','ps_properties.txt']:shutil.copy2(R/'cpu_767_proposal'/name,stage/'cpu_767_offline_only'/name)
files=sorted(f for f in stage.rglob('*') if f.is_file() and f.name!='SHA256SUMS')
(stage/'SHA256SUMS').write_text(''.join(digest(f)+'  '+str(f.relative_to(stage))+'\n' for f in files))
archive=stage.with_suffix('.tar.gz')
with tarfile.open(archive,'w:gz') as t:t.add(stage,arcname=stage.name)
with tarfile.open(archive) as t:
 for f in files+[stage/'SHA256SUMS']:assert t.extractfile(stage.name+'/'+str(f.relative_to(stage))).read()==f.read_bytes()
(R/'results/package_verified.json').write_text(json.dumps({'pass':True,'archive':str(archive),'sha256':digest(archive),'files_verified':len(files)+1},indent=2)+'\n')
print('PASS archive',digest(archive),len(files)+1)
