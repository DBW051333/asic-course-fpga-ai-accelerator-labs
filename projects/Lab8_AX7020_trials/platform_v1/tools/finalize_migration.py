"""Validate target evidence and create a hash-verified AX7020 deployment package."""
from pathlib import Path
import hashlib,json,re,shutil,tarfile,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
meta=json.loads((R/'migration.json').read_text());P=Path(meta['direct_source_project'])
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((R/'results'/name).read_text())
for name,h in meta['model_sha256'].items():assert digest(R/name)==h,name
for p in (P/'rtl').rglob('*.v'):
 q=R/p.relative_to(P);assert p.read_text().replace(str(P),'<ROOT>')==q.read_text().replace(str(R),'<ROOT>'),p
for name,h in json.loads((R/'evidence/source/source_manifest.json').read_text()).items():assert digest(P/name)==h, name
baselines=json.loads(Path('/home/ding/vivado_project/Lab8_baselines/baselines.json').read_text())['baselines']
for b in baselines:
 for name,h in json.loads(Path(b['checksum_manifest']).read_text()).items():assert digest(Path(b['project_root'])/name)==h,name
for name in ['simulation_axis.json','simulation_dma.json','python_tests.json','reference_verified.json','checkpoint_verified.json','dsp_audit.json','fc2_register_audit.json','boundary_checks.json']:assert read(name)['pass'],name
for v in read('dma_schedule.json')['results'].values():assert v['total_cycles']==7423 and v['feature_values_checked']==6804
axis=(R/'simulation/axis/xsim.console.log').read_text();assert 'compute_cycles=216..216' in axis and 'PASS BATCH INTEGRATED samples=94 values=15228 min_ii=172' in axis
hwh=ET.parse(R/'overlay/lab8.hwh')
dma=hwh.find(".//MODULE[@INSTANCE='axi_dma_0']")
addresses=[dict(x.attrib) for x in dma.findall('.//MEMRANGE')]
assert len(addresses)==2 and {x['MASTERBUSINTERFACE'] for x in addresses}=={'M_AXI_MM2S','M_AXI_S2MM'}
assert all(int(x['BASEVALUE'],0)==0 and int(x['HIGHVALUE'],0)==0x3fffffff for x in addresses)
ps=hwh.find(".//MODULE[@INSTANCE='processing_system7_0']")
params={p.attrib['NAME']:p.attrib['VALUE'] for p in ps.findall('./PARAMETERS/PARAMETER')}
for key,value in {'PCW_CRYSTAL_PERIPHERAL_FREQMHZ':'33.333333','PCW_DDR_RAM_HIGHADDR':'0x3FFFFFFF','PCW_FCLK0_PERIPHERAL_DIVISOR0':'7','PCW_FCLK0_PERIPHERAL_DIVISOR1':'1','PCW_UART1_PERIPHERAL_ENABLE':'1','PCW_UART0_PERIPHERAL_ENABLE':'0'}.items():assert params[key]==value,(key,params.get(key))
assert 'xc7z020clg400-2' in (R/'results/build_complete.txt').read_text()
resources={}
for key,label in {'lut':'Slice LUTs','ff':'Slice Registers','bram36_equivalent':'Block RAM Tile','dsp':'DSPs','slice':'Slice'}.items():
 m=re.search(r'\|\s*'+re.escape(label)+r'\s*\|\s*([\d.]+)\s*\|',(R/'results/utilization.rpt').read_text());assert m,label;resources[key]=float(m[1])
assert resources['dsp']==212 and resources['bram36_equivalent']==56
assert 'All user specified timing constraints are met.' in (R/'results/timing_summary.rpt').read_text()
source=json.loads((R/'evidence/source/summary.json').read_text())
summary={'pass':True,'project_id':meta['project_id'],'source_baseline':meta['source_baseline'],'direct_source_project':str(P),'target_board':'AX7020','part':meta['part'],'resources':resources,'resource_change_vs_direct_parent':{k:resources[k]-source['resources'][k] for k in resources},'timing':read('checkpoint_verified.json'),'core_cycles':216,'batch_start_interval_cycles':172,'dma_42_simulation_cycles':7423,'target_clock_hz':166666672,'dma_hwh_address_ranges':addresses,'model_identical':True,'functional_rtl_identical':True,'parent_and_designated_baselines_verified':True,'default_changed':False,'known_warnings':meta.get('known_warnings',[]),'board_tested':False,'power_measured':False,'scope':'Fresh target RTL, AMD DMA IP simulation, full implementation and reopened final DCP. Board results recorded separately.'}
board=R/'results/board/board_acceptance/acceptance.json'
if board.exists():
 a=json.loads(board.read_text());summary['board_tested']=True;summary['board_acceptance_pass']=a['pass'];summary['clock_board']=a.get('clock')
bench=R/'results/board/api_board_results.json'
if bench.exists():summary['api_benchmark_completed']=True
summary['designated_baseline_comparisons']=[{'baseline_id':b['id'],'core_cycles':b['core_cycles'],'resource_change':{k:resources[k]-b['resources'][k] for k in resources}} for b in baselines]
(R/'results/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
meta['verification'].update(simulation='passed',implementation='passed',board='passed' if summary.get('board_acceptance_pass') else 'pending')
meta['summary']=str(R/'results/summary.json');(R/'migration.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
stage=R/'deploy/lab8_ax7020_192';stage.mkdir(exist_ok=True)
for p in (R/'ps').iterdir():
 if p.is_file() and p.suffix in ('.py','.bin','.json','.ipynb'):shutil.copy2(p,stage/p.name)
for name in ['lab8.bit','lab8.hwh']:shutil.copy2(R/'overlay'/name,stage/name)
shutil.copy2(R/'overlay/lab8.xsa',stage/'lab8_ax7020_192.xsa')
if (stage/'lab8.xsa').exists():(stage/'lab8.xsa').unlink()
for name in ['README.md','migration.json']:shutil.copy2(R/name,stage/name)
shutil.copy2(R/'results/summary.json',stage/'implementation_summary.json')
if (R/'results/board_report.md').exists():shutil.copy2(R/'results/board_report.md',stage/'board_report.md')
if (R/'results/board').exists():shutil.copytree(R/'results/board',stage/'board_evidence',dirs_exist_ok=True)
files=sorted(p for p in stage.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
(stage/'SHA256SUMS').write_text(''.join(digest(p)+'  '+str(p.relative_to(stage))+'\n' for p in files))
archive=stage.with_suffix('.tar.gz')
with tarfile.open(archive,'w:gz') as t:t.add(stage,arcname=stage.name)
with tarfile.open(archive) as t:
 for p in files+[stage/'SHA256SUMS']:assert t.extractfile(stage.name+'/'+str(p.relative_to(stage))).read()==p.read_bytes()
(R/'results/package_verified.json').write_text(json.dumps({'pass':True,'archive':str(archive),'sha256':digest(archive),'verified_files':len(files)+1},indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
