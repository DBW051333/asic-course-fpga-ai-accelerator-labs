from pathlib import Path
import hashlib,json,shutil,tarfile,difflib
R=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text())
meta=read('experiment.json')
for manifest,parent in [('software_parent_manifest.json',Path(meta['direct_parent_root'])),('hardware_parent_manifest.json',Path(meta['hardware_parent']))]:
 for name,h in read('evidence/'+manifest).items():assert digest(parent/name)==h,name
assert (R/'ps/parent_driver.py').read_bytes()==(Path(meta['direct_parent_root'])/'ps/lab8_driver.py').read_bytes()
for f in (Path(meta['hardware_parent'])/'data').rglob('*'):
 if f.is_file():assert digest(R/f.relative_to(Path(meta['hardware_parent'])))==digest(f),f
for b in json.loads(Path('/home/ding/vivado_project/Lab8_baselines/baselines.json').read_text())['baselines']:
 for name,h in json.loads(Path(b['checksum_manifest']).read_text()).items():assert digest(Path(b['project_root'])/name)==h,name
assert json.loads(Path('/home/ding/vivado_project/Lab8_baselines/current_project.json').read_text())==read('evidence/current_project_before.json')
for file in ['checkpoint_verified','dsp_audit','reference_verified','simulation_axis','simulation_dma','python_tests']:
 assert read('results/'+file+'.json')['pass'],file
c=read('results/board/comparison.json');a=read('results/board/board_acceptance/acceptance.json');s=read('results/board/stress_results.json');f=read('results/board/dma_fault_results.json')
assert all(v['pass'] for v in [c,a,s,f])
assert len(c['blocks'])==8
assert all(v['variants'][t]['samples']==400 for v in c['aggregated'] for t in ['A','B'])
for name,folder in [('lab8.bit','overlay'),('lab8.hwh','overlay'),('lab8_driver.py','ps'),('parent_driver.py','ps'),('parent.bit','ps'),('parent.hwh','ps')]:assert c['hashes'][name]==digest(R/folder/name),name
assert a['hashes']['lab8.bit']==digest(R/'overlay/lab8.bit')
assert s['driver_sha256']==f['driver_sha256']==digest(R/'ps/lab8_driver.py')
assert all(row['compute_cycles']==216 for block in c['blocks'] for m in block['measurements'] for row in m['raw'])
assert all(m['stats']['pl_transaction_cycles']['median']==(m['N']-1)*172+285 for block in c['blocks'] for m in block['measurements'] if m['mode']=='batch')
extra=[row['pl_transaction_cycles']-((m['N']-1)*172+285) for block in c['blocks'] for m in block['measurements'] if m['mode']=='batch' for row in m['raw']]
assert min(extra)>=0
extra_summary={'transactions':len(extra),'nonzero_extra_cycle_transactions':sum(v>0 for v in extra),'max_extra_cycles':max(extra),'all_batch_medians_match_formula':True}
stress=next(v for v in s['phases'] if v['name']=='continuous_120_seconds');assert stress['elapsed_seconds']>=120 and stress['errors']==0
main=next(v for v in c['aggregated'] if v['N']==4096);success=main['api_median_reduction_percent']>=5
summary={'pass':True,'project_id':meta['project_id'],'source_baseline':meta['source_baseline'],'direct_parent_id':meta['direct_parent_id'],'primary_metric':meta['primary_metric'],'primary_metric_target_met':success,'api_results':c['aggregated'],'board_clock':a['clock'],'routed_timing':read('results/checkpoint_verified.json'),'resources':{'lut':14312,'ff':18905,'bram36_equivalent':56,'dsp':212},'core_cycles':216,'II_cycles':172,'course_correct':42,'feature_values_checked':6804,'stress':stress,'dma_faults':f['phases'],'parents_and_baselines_protected':True,'current_selection_preserved':True,'arm_ddr_changed':False,'batch_extra_cycles':extra_summary,'cpu_767_scope':'offline PS-only XSA proposal; not deployed or board verified','ddr_scope':'existing application path measured; no extra PL stalls, no burst/DDR retiming deployed','power_measured':False,'maximum_batch_16383_board_tested':False,'200mhz_board_tested':False}
(R/'results/optimization_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
meta.update(status='verified',primary_metric_target_met=success,summary=str(R/'results/optimization_summary.json'))
(R/'experiment.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
(R/'results/driver.diff').write_text(''.join(difflib.unified_diff((R/'ps/parent_driver.py').read_text().splitlines(True),(R/'ps/lab8_driver.py').read_text().splitlines(True),fromfile='ps_api_v3',tofile='platform_v1')))
print('PASS board evidence, parents, baselines and default protection; primary >=5%:',success)
