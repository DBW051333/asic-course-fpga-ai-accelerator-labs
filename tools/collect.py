from pathlib import Path
import hashlib,json,shutil,re
ROOT=Path(__file__).resolve().parents[1];BASE=Path('/home/ding/vivado_project');COURSE=Path('/home/ding/桌面/Lab')
PROJECTS=['Lab1','Lab1_re','Lab2_4_to_1','Lab2_8_3_encoder','Lab3_sync_fifo','aync_fifo','Lab4','Lab4_tree4_1221_full4p3','Lab5','Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8','Lab6','Lab6_architecture_trials/fc2_interleaved_split11','Lab6_growth_trials/fc1_128x6_dual']
SHARED=['Lab5_optimization/data','Lab5_optimization/tools','Lab5_truncation_optimization/data','Lab6_three_version_comparison']
EXT={'.v','.sv','.vh','.vhd','.vhdl','.xdc','.xpr','.xci','.bd','.tcl','.py','.coe','.mem','.mif','.hex','.txt','.csv','.json','.md','.rpt','.log','.wcfg','.pdf','.pptx','.docx','.doc','.wps','.bit','.npy','.npz'}
CHECKPOINTS={'Lab4_tree4_1221_full4p3/Lab4.runs/impl_1/fc_top_routed.dcp','Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/results/explore_routed.dcp','Lab6_architecture_trials/fc2_interleaved_split11/results/final_routed.dcp','Lab6_growth_trials/fc1_128x6_dual/results/final_routed.dcp'}
records={}
def skip(p,base):
    parts=p.relative_to(base).parts
    return any(x.startswith('.') or x in {'安装包','ipstatic','xsim.dir'} or x.endswith(('.cache','.gen','.sim','.ip_user_files','.hw')) for x in parts)
def copy(p,base,category):
    rel=p.relative_to(base);dest=ROOT/category/rel
    if dest.exists():return
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    records[str(dest.relative_to(ROOT))]={'source':str(p),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def include(p):
    if not p.is_file() or skip(p,BASE):return
    rel=p.relative_to(BASE)
    if str(rel) in CHECKPOINTS:copy(p,BASE,'projects');return
    parts=rel.parts
    if any(x.endswith('.runs') for x in parts) and p.suffix not in {'.rpt','.log','.tcl'}:return
    if p.suffix.lower() not in EXT:return
    if '.backup.' in p.name or p.name.startswith(('vivado_','simulation_pipeline_check_')):return
    if 'ip' in parts and p.suffix not in {'.xci','.coe','.mem','.mif','.xdc'}:return
    if p.stat().st_size>=45*1024**2:return
    copy(p,BASE,'projects')
for name in PROJECTS+SHARED:
    for p in (BASE/name).rglob('*'):include(p)
for name in ['Lab4_optimized','Lab5_optimization','Lab5_truncation_optimization','Lab6_bottleneck_optimization','Lab6_limit_search','Lab6_architecture_trials','Lab6_growth_trials']:
    for p in (BASE/name).glob('*.md'):include(p)
    for p in (BASE/name/'tools').glob('*'):include(p)
for p in COURSE.rglob('*'):
    if p.is_file() and not skip(p,COURSE) and p.suffix.lower() in EXT:copy(p,COURSE,'course_materials')
for p in (COURSE/'.document_edit').glob('*'):
    if p.is_file() and p.suffix in {'.doc','.docx','.wps'}:copy(p,COURSE,'course_materials')
for p in (COURSE/'.document_edit/final_rendered').glob('*.pdf'):copy(p,COURSE,'course_materials')
# Resolve literal references to data and source files.
for turn in range(5):
    before=len(records)
    for dest in list(records):
        p=ROOT/dest
        if p.suffix not in {'.v','.sv','.vh','.tcl','.py','.xci','.xpr','.bd'}:continue
        content=p.read_text(errors='ignore')
        for match in re.findall(r'''/home/ding/vivado_project/[^\s"'<>;{}\[\]()]+''',content):
            source=Path(match)
            if source.is_file() and source.suffix.lower() in {'.mem','.coe','.mif','.hex','.v','.sv','.vh','.tcl','.py','.json','.txt'}:include(source)
    if len(records)==before:break
(ROOT/'manifests').mkdir(exist_ok=True)
(ROOT/'manifests/files.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
(ROOT/'manifests/selection.json').write_text(json.dumps({'representative_projects':PROJECTS,'shared_dependencies':SHARED,'checkpoints':sorted(CHECKPOINTS)},ensure_ascii=False,indent=2)+'\n')
print('files',len(records),'MiB',round(sum(x['size'] for x in records.values())/1024**2,1))
