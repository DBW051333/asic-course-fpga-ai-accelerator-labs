"""Validate software-only AX7020 evidence, provenance and a reproducible package."""
from pathlib import Path
import hashlib,json,shutil,tarfile,difflib
R=Path(__file__).resolve().parents[1];meta=json.loads((R/'experiment.json').read_text());P=Path(meta['direct_parent_root'])
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text())
for name,h in read('evidence/parent_manifest.json').items():assert digest(P/name)==h, name
assert (R/'ps/parent_driver.py').read_bytes()==(P/'ps/lab8_driver.py').read_bytes()
for folder in ['rtl','data']:
 for f in (P/folder).rglob('*'):
  if f.is_file():assert digest(R/f.relative_to(P))==digest(f),f
for name in ['lab8.bit','lab8.hwh','lab8.xsa']:assert digest(R/'overlay'/name)==digest(P/'overlay'/name),name
baselines=json.loads(Path('/home/ding/vivado_project/Lab8_baselines/baselines.json').read_text())['baselines']
for b in baselines:
 for name,h in json.loads(Path(b['checksum_manifest']).read_text()).items():assert digest(Path(b['project_root'])/name)==h,name
current=json.loads(Path('/home/ding/vivado_project/Lab8_baselines/current_project.json').read_text());assert current==read('evidence/current_project_before.json')
assert read('results/python_tests.json')['pass'] and read('results/python_tests.json')['tests']>=15
assert read('results/reference_verified.json')['pass']
a=read('results/board/board_acceptance/acceptance.json');s=read('results/board/stress_results.json');c=read('results/board/comparison.json');scalar=read('results/board/board_scalar/summary.json');batch=read('results/board/batch_board_results.json')
assert a['pass'] and s['pass'] and c['pass']
assert scalar['correct']==42 and scalar['feature_values_checked']==6804 and scalar['hardware_errors']==0
assert batch['samples']==42 and batch['last_sample_features_checked']
assert len(c['blocks'])==8 and c['order']==['A','B','B','A','A','B','B','A']
assert all(v['variants']['A']['samples']==400 and v['variants']['B']['samples']==400 for v in c['aggregated'])
for name,folder in [('lab8.bit','overlay'),('lab8.hwh','overlay'),('lab8_driver.py','ps'),('parent_driver.py','ps')]:
 assert c['hashes'][name]==digest(R/folder/name),name
 assert a['hashes'][name]==digest(R/folder/name),name
assert s['driver_sha256']==digest(R/'ps/lab8_driver.py')
fault=read('results/board/dma_fault_results.json')
assert fault['pass'] and fault['driver_sha256']==digest(R/'ps/lab8_driver.py')
assert len(fault['phases'])==2 and all(p['pass'] for p in fault['phases'])
assert int(fault['phases'][1]['status_before_reset']['recv'],16)&0x70
pilot=read('results/board/pilot_valid.json')
assert pilot['pass']
assert pilot['hashes']['compare_api.py']==digest(R/'evidence/pilot_compare_api.py')
assert pilot['hashes']['lab8_driver.py']==digest(R/'ps/prototype2_driver.py')
assert pilot['hashes']['prototype1_driver.py']==digest(R/'ps/prototype1_driver.py')
assert pilot['hashes']['parent_driver.py']==digest(R/'ps/parent_driver.py')
assert read('results/board/parse_microbench.json')['results']
# No DMA or scalar changes are allowed in this parsing experiment.
import ast
parent_class=next(v for v in ast.parse((R/'ps/parent_driver.py').read_text()).body if isinstance(v,ast.ClassDef))
candidate_class=next(v for v in ast.parse((R/'ps/lab8_driver.py').read_text()).body if isinstance(v,ast.ClassDef))
for method in parent_class.body:
 if isinstance(method,ast.FunctionDef) and method.name!='infer_batch':
  other=next(v for v in candidate_class.body if isinstance(v,ast.FunctionDef) and v.name==method.name)
  assert ast.dump(method)==ast.dump(other),method.name
main=next(v for v in c['aggregated'] if v['mode']=='batch' and v['N']==42)
assert main['api_median_reduction_percent']>=meta['minimum_reduction_percent']
assert all(v['api_p95_reduction_percent']>=-5 and v['api_median_reduction_percent']>=-5 for v in c['aggregated'])
assert [v['N'] for v in c['aggregated'] if v['mode']=='batch']==[1,2,3,8,16,42,48,49,64,96,128,256,512]
assert all(row['compute_cycles']==216 for block in c['blocks'] for m in block['measurements'] for row in m['raw'])
stress=next(p for p in s['phases'] if p['name']=='continuous_120_seconds');assert stress['elapsed_seconds']>=120 and stress['errors']==0
summary={'pass':True,'project_id':meta['project_id'],'source_baseline':meta['source_baseline'],'direct_parent_id':meta['direct_parent_id'],'primary_metric':meta['primary_metric'],'primary_api_median_reduction_percent':main['api_median_reduction_percent'],'primary_p95_reduction_percent':main['api_p95_reduction_percent'],'api_results':c['aggregated'],'software_only':True,'hardware_artifacts_identical':True,'model_rtl_identical':True,'hardware_evidence_reused':str(R/'evidence/hardware'),'resources':read('evidence/hardware/summary.json')['resources'],'core_cycles':216,'batch_ii_simulation_reused':172,'board_clock':a['clock'],'functional_acceptance_pass':True,'course_accuracy':'42/42','course_feature_values':6804,'dma_faults':fault['phases'],'decoder_switch_N':48,'host_tests':read('results/python_tests.json')['tests'],'stress':stress,'parent_and_baselines_protected':True,'current_selection_preserved':True,'power_measured':False,'new_implementation_run':False,'maximum_batch_16383_board_tested':False,'scope':'New AX7020 software A/B and board functional/reliability validation. Identical RTL/model/bit/hwh; prior routed resources/timing reused, not newly implemented.'}
(R/'results/optimization_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
meta.update(status='verified',summary=str(R/'results/optimization_summary.json'),verification={'host':'passed','board_acceptance':'passed','AB_full_API':'passed','stress_120s':'passed','real_dma_fault_recovery':'passed','hardware':'unchanged; prior implementation evidence reused'})
(R/'experiment.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
# Keep the exact measured identities separately before adding report/package metadata.
measured={name:c['hashes'][name] for name in c['hashes'] if name in ['lab8.bit','lab8.hwh','lab8_driver.py','parent_driver.py','prototype1_driver.py','prototype2_driver.py','compare_api.py','inputs.bin','features.bin','predictions.bin']}
(R/'evidence/measured_manifest.json').write_text(json.dumps(measured,indent=2)+'\n')
import subprocess,sys
subprocess.run([sys.executable,str(R/'tools/write_report.py')],check=True)
stage=R/'deploy/lab8_ax7020_ps_api_v3';stage.mkdir(parents=True,exist_ok=True)
for f in (R/'ps').iterdir():
 if f.is_file() and f.suffix in ('.py','.bin','.json','.ipynb'):shutil.copy2(f,stage/f.name)
for name in ['lab8.bit','lab8.hwh']:shutil.copy2(R/'overlay'/name,stage/name)
shutil.copy2(R/'overlay/lab8.xsa',stage/'lab8_ax7020_192.xsa')
for name in ['README.md','experiment.json']:shutil.copy2(R/name,stage/name)
shutil.copy2(R/'results/optimization_summary.json',stage/'optimization_summary.json')
if (R/'results/optimization_report.md').exists():shutil.copy2(R/'results/optimization_report.md',stage/'optimization_report.md')
shutil.copytree(R/'results/board',stage/'board_evidence',dirs_exist_ok=True)
(stage/'profile_evidence').mkdir(exist_ok=True)
for f in (R/'results/board').glob('profile_*'):shutil.copy2(f,stage/'profile_evidence'/f.name)
shutil.copy2(R/'results/board/pilot_valid.json',stage/'pilot.json');shutil.copy2(R/'results/driver.diff',stage/'driver.diff')
shutil.copy2(R/'evidence/measured_manifest.json',stage/'measured_manifest.json')
shutil.copytree(R/'evidence',stage/'provenance',dirs_exist_ok=True)
files=sorted(f for f in stage.rglob('*') if f.is_file() and f.name!='SHA256SUMS')
(stage/'SHA256SUMS').write_text(''.join(digest(f)+'  '+str(f.relative_to(stage))+'\n' for f in files))
archive=stage.with_suffix('.tar.gz')
with tarfile.open(archive,'w:gz') as t:t.add(stage,arcname=stage.name)
with tarfile.open(archive) as t:
 for f in files+[stage/'SHA256SUMS']:assert t.extractfile(stage.name+'/'+str(f.relative_to(stage))).read()==f.read_bytes()
(R/'results/package_verified.json').write_text(json.dumps({'pass':True,'archive':str(archive),'sha256':digest(archive),'files_verified':len(files)+1,'measured_identities_match':True},indent=2)+'\n')
print('PASS software-only provenance, new board evidence, API target and archive verification')
