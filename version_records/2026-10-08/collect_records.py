from pathlib import Path
import json,hashlib,tarfile,csv,io,re,subprocess
BASE=Path('/home/ding/vivado_project');OUT=Path(__file__).resolve().parent;REPO=Path('/home/ding/桌面/Lab_代表版本备份')
if (OUT/'versions.json').exists():raise SystemExit('Historical records already exist; refusing to overwrite them after cleanup.')
selection=json.loads((REPO/'manifests/selection.json').read_text());KEEP=selection['representative_projects']
GROUPS=['Lab5_optimization','Lab5_truncation_optimization','Lab6_bottleneck_optimization','Lab6_limit_search','Lab6_architecture_trials','Lab6_growth_trials']
versions=[]
for p in BASE.iterdir():
 if p.is_dir() and not p.is_symlink() and p.name.startswith(('Lab1','Lab2','Lab3','Lab4','Lab5','Lab6')) and p.name not in GROUPS and p.name!='Lab6_three_version_comparison':versions.append(p)
for g in GROUPS:
 for p in (BASE/g).iterdir():
  if p.is_dir() and p.name not in {'data','tools','results','rtl','.Xil','__pycache__'}:versions.append(p)
versions.append(BASE/'aync_fifo');versions=sorted(set(versions))
assert all(BASE/k in versions for k in KEEP)
EXT={'.coe','.mem','.mif','.hex','.txt','.csv','.json','.md','.rpt','.log','.jou','.xdc','.npy','.npz','.dat'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(4*1024*1024),b''):h.update(x)
 return h.hexdigest()
def retain(p,root):
 parts=p.relative_to(root).parts
 if any(x in {'.Xil','xsim.dir','ipstatic','__pycache__'} or x.endswith(('.cache','.gen','.ip_user_files')) for x in parts):return False
 if p.suffix.lower() not in EXT:return False
 return True
# Preserve source files already referenced in the representative backup, plus literal RTL/IP data references.
protected=set()
for e in json.loads((REPO/'manifests/files.json').read_text()).values():
 p=Path(e['source'])
 if p.is_relative_to(BASE) and p.is_file():protected.add(str(p))
for k in KEEP:
 for p in (BASE/k).rglob('*'):
  if not p.is_file() or p.suffix not in {'.v','.sv','.vh','.xci','.bd'}:continue
  if any(x.endswith(('.cache','.gen','.sim','.runs','.ip_user_files')) or x in {'.Xil','xsim.dir'} for x in p.parts):continue
  for match in re.findall(r'''/home/ding/vivado_project/[^\s"'<>;{}\[\]()]+''',p.read_text(errors='ignore')):
   dep=Path(match)
   if dep.is_file():protected.add(str(dep))
# Preserve all shared data and runner tools; these are dependencies, not extra active project versions.
for g in GROUPS:
 for shared in ['data','tools','rtl']:
  for p in (BASE/g/shared).rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:protected.add(str(p))
(OUT/'protected_dependencies.json').write_text(json.dumps(sorted(protected),ensure_ascii=False,indent=2)+'\n')
summary_cache={}
for g in GROUPS:
 entries=[]
 for p in (BASE/g/'results').glob('*.json'):
  try:obj=json.loads(p.read_text())
  except:continue
  if isinstance(obj,list):entries.extend({'source':str(p.relative_to(BASE)),'value':x} for x in obj if isinstance(x,dict) and 'name' in x)
  elif isinstance(obj,dict) and 'name' in obj:entries.append({'source':str(p.relative_to(BASE)),'value':obj})
 summary_cache[g]=entries
registry=[];inventory=[]
for root in versions:
 name=str(root.relative_to(BASE));kept=name in KEEP;archive=OUT/(name.replace('/','__')+'.tar.gz');files=[];allocated=0
 with tarfile.open(archive,'w:gz',compresslevel=1) as tar:
  for p in sorted(root.rglob('*')):
   if p.is_symlink():continue
   if not p.is_file():continue
   stat=p.stat();yes=retain(p,root);allocated+=stat.st_blocks*512
   f={'path':str(p.relative_to(root)),'size':stat.st_size,'mtime_ns':stat.st_mtime_ns,'allocated_bytes':stat.st_blocks*512,'sha256':sha(p),'recorded':yes,'protected_dependency':str(p) in protected};files.append(f)
   if yes:tar.add(p,arcname=f['path'],recursive=False)
 with tarfile.open(archive,'r:gz') as tar:
  expected={f['path']:f for f in files if f['recorded']};assert set(tar.getnames())==set(expected)
  for n,f in expected.items():assert hashlib.sha256(tar.extractfile(n).read()).hexdigest()==f['sha256']
 local={}
 for p in (root/'results').glob('*.json'):
  try:local[str(p.relative_to(root))]=json.loads(p.read_text())
  except:pass
 if (root/'config.json').exists():local['config.json']=json.loads((root/'config.json').read_text())
 matched=[e for e in summary_cache.get(root.parent.name,[]) if e['value'].get('name')==root.name]
 metrics={}
 if matched:metrics.update(matched[0]['value'])
 for key in ['results/final_clock.json','results/final_clock_explore.json']:
  if isinstance(local.get(key),dict):metrics.update(local[key])
 statuses=local.get('results/run_status.json',{})
 for field in ['sim','synth','impl','final_verify']:
  if isinstance(statuses.get(field),dict):metrics[field]=statuses[field].get('status')
 errors=[]
 for f in files:
  if not f['recorded'] or Path(f['path']).suffix not in {'.log','.rpt'}:continue
  p=root/f['path']
  for line in p.read_text(errors='ignore').splitlines():
   if line.startswith('ERROR:') or 'errors=0' in line or 'errors = 0' in line:
    if line not in [e['text'] for e in errors]:errors.append({'file':f['path'],'text':line})
  if len(errors)>30:break
 item={'version':name,'keep_project':kept,'policy':'保留代表工程' if kept else '仅留配置、数据与验证记录，移除工程','allocated_bytes_before':allocated,'archive':archive.name,'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'recorded_files':sum(f['recorded'] for f in files),'total_files':len(files),'reported_metrics':metrics,'metric_sources':matched,'local_json_snapshots':local,'evidence_excerpts':errors[:30],'report_paths':[f['path'] for f in files if Path(f['path']).suffix=='.rpt' and f['recorded']]}
 registry.append(item);inventory.append({'version':name,'files':files})
 print(name,'KEEP' if kept else 'RECORD ONLY',flush=True)
# Shared group summaries and root reports cover comparisons that are not isolated project directories.
context=OUT/'context';context.mkdir(exist_ok=True)
for g in GROUPS:
 for p in (BASE/g).rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(BASE/g)
  if (len(rel.parts)==1 and p.suffix=='.md') or (len(rel.parts)==2 and rel.parts[0]=='results' and p.suffix in {'.json','.csv','.md','.txt','.rpt','.log'}):
   import shutil
   d=context/g/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
# Include original comparison narratives, so older Lab4 variants have their measured metrics and interpretation.
import shutil
p=BASE/'Lab4_optimized/adder_experiments'
if p.exists():
 for f in p.glob('*.md'):
  d=context/'Lab4'/f.name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
(OUT/'versions.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
(OUT/'file_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
with (OUT/'versions.csv').open('w',newline='') as f:
 cols=['version','keep_project','sim','synth','impl','cycles','interval_cycles','period','latency_ns','lut','ff','bram','dsp','wns','whs','archive','recorded_files'];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for x in registry:
  row={k:x.get(k,'') for k in cols};row.update({k:x['reported_metrics'].get(k,'') for k in cols if k not in x});w.writerow(row)
lines=['# 全版本数据记录与代表工程保留清单','','日期：2026-10-08。共清点现存版本目录 %d 个：保留 13 个代表工程，其余 %d 个版本记录后移除。前一轮已删除的 7 组失败试验另见 `../../失败试验记录/2026-10-08/`（GitHub 对应 `failed_experiments/2026-10-08/`）。本记录覆盖所有发现的版本，包括通过、失败、取消、未完成和旧 recommended 导出副本；删除不代表判定该版本功能失败。'%(len(registry),len(registry)-len(KEEP)),'','## 保留工程','','\n'.join('- `'+k+'`' for k in KEEP),'','Lab1/2/3 保留课程基础工程，仍以原报告中的验证范围为准；保留目录不等于新增了上板或完整 CDC 验证。Lab4 保留课程原版与 4.3 ns 最终版；Lab5 保留课程原版与未截位流式版；Lab6 保留原 8/4 位参考、资源较省版和高并行版。其他正确但重复/较慢的版本只保存记录。','','## 数据与证据','','- `versions.csv`：便于比较的指标表；空项表示未从结构化数据取得，不能当作 0 或未通过。','- `versions.json`：每版配置、运行状态、全部本地 JSON 快照、中央汇总原记录及其路径、错误摘录和报告索引。不同日期/约束/综合与布线口径不可混用；中央汇总可能过期，原日志与最后的 run_status/final_clock 优先。','- 每版 `.tar.gz`：输入与权重数据、配置 JSON/XDC、数值输出、日志、资源及时序报告、说明。仅记录数据；不保留未选中版本的 RTL/TB/XPR、DCP、波形与构建数据库。','- `file_inventory.json`：删除前所有文件大小、SHA-256、时间、哪些内容进入记录以及哪些共享依赖需继续存在。','- `context/`：各轮完整比较数据、量化范围证明、资源演进及停止判断，保留原始口径。','- `protected_dependencies.json`：被保留工程引用的文件及共享工具、数据，不作为额外工程版本。','- `cleanup_receipt.json`：在本地和 GitHub 记录均通过校验后执行的删除清单与空间统计。','','本次未重跑功能仿真或布局布线，不把仅数值正确、未完成试验或历史标题中的 recommended 作为当前最佳。代表工程按已核实的最终记录选择。保留工程中的历史对比/搜索脚本若依赖被移除的旧工程，需要查阅本记录；正常代表版本的源码和初始化数据依赖保留。','','大部分版本的原始数值/资源数据已保存；对于从未生成报告或已缺失的测量，本记录明确留空，不虚构结果。用户需要进一步追溯时，应查看对应压缩包内的原始报告。']
(OUT/'README.md').write_text('\n'.join(lines)+'\n')
print('TOTAL',len(registry),'record archive MiB',sum(x['archive_bytes'] for x in registry)/1024**2,'removable GiB',sum(x['allocated_bytes_before'] for x in registry if not x['keep_project'])/1024**3,flush=True)
