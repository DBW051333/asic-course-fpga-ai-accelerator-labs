from pathlib import Path
import os,json,hashlib,tarfile,io,subprocess
BASE=Path('/home/ding/vivado_project');OUT=Path(__file__).resolve().parent
TARGETS={
'Lab4_tree4_1221_clk4p2':'4.2 ns 目标下 Setup WNS -0.029 ns，4 个失败端点；128 项数值通过，仍未通过目标时序。代表 4.3 ns 最终版本保留。',
'Lab6_limit_search/dual512_lookup':'仿真 7776 项错误 0，107 拍/间隔65；实现因 CARRY4 14014 > 13300 失败。',
'Lab6_limit_search/dual512_hybrid':'混合树仿真通过，106 拍/间隔65；最终 run_status 记录综合通过、实现失败。Place 30-4/30-99：利用率过高，布局初始化失败；旧 comparison 的 running/not_run 是过期摘要。',
'Lab6_limit_search/dual512_full_lookup':'仿真及综合通过；Place 30-487：剩余 1453 slices，而未放置单元需要 1715，详细布局失败。',
'Lab6_limit_search/phys_bram_register':'Vivado 2025.2 布线后 phys_opt_design 不支持 -dsp_register_opt/-bram_register_opt，命令失败；不是数值失败。',
'Lab6_limit_search/prepack_address_banks':'共享大 ROM 多读端口综合展开并造成内存压力，主动终止；run_status synth returncode -15。不是已完成综合后的数值/资源结论。',
'Lab6_dsp_multipump_probe':'16 DSP 倍频原型：最终 2048 帧/131072 独立乘积错误0；修正版 WNS -1.825 ns、WHS -3.343 ns；MMCM启动相位未验证、未集成整网，时序失败。保留初版、修正版、对照及所有历史错误日志。'
}
EXT={'.v','.sv','.vh','.vhd','.vhdl','.xdc','.tcl','.py','.coe','.mem','.mif','.hex','.txt','.csv','.json','.md','.rpt','.log','.jou','.xpr','.xci','.bd','.wcfg','.xml','.prj'}
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def retain(p,root):
 rel=p.relative_to(root);parts=rel.parts
 if any(x in {'.Xil','xsim.dir','ipstatic','__pycache__'} or x.endswith(('.cache','.gen','.sim','.ip_user_files')) for x in parts):return False
 if p.suffix.lower() not in EXT:return False
 if any(x.endswith('.runs') for x in parts) and p.suffix.lower() not in {'.log','.rpt','.tcl','.jou'}:return False
 if 'ip' in parts and p.suffix.lower() not in {'.xci','.coe','.mem','.mif','.xdc'}:return False
 return True
entries=[]
for name,reason in TARGETS.items():
 root=BASE/name;files=[];allocated=0
 assert root.is_dir() and not root.is_symlink(),name
 archive=OUT/(name.replace('/','__')+'.tar.gz')
 with tarfile.open(archive,'w:gz') as tar:
  for p in sorted(root.rglob('*')):
   if p.is_symlink():raise RuntimeError('Unexpected symlink: '+str(p))
   if not p.is_file():continue
   stat=p.stat();keep=retain(p,root);allocated+=stat.st_blocks*512
   info={'path':str(p.relative_to(root)),'size':stat.st_size,'mtime_ns':stat.st_mtime_ns,'sha256':digest(p),'retained':keep};files.append(info)
   if keep:tar.add(p,arcname=info['path'],recursive=False)
 with tarfile.open(archive,'r:gz') as tar:
  members={x.name:x for x in tar.getmembers()}
  assert set(members)=={x['path'] for x in files if x['retained']}
  for e in files:
   if e['retained']:assert hashlib.sha256(tar.extractfile(e['path']).read()).hexdigest()==e['sha256'],e['path']
 entries.append({'source':str(root),'reason':reason,'archive':archive.name,'archive_size':archive.stat().st_size,'archive_sha256':digest(archive),'allocated_bytes_before':allocated,'files':files})
 print(name,'retained',sum(e['retained'] for e in files),'/',len(files),'archive MiB',round(archive.stat().st_size/1024**2,2),flush=True)
# Save contextual summaries and authoritative reports which live outside deleted projects.
context=OUT/'context';context.mkdir(exist_ok=True)
paths=[BASE/'Lab6_limit_search/results/comparison.json',BASE/'Lab6_limit_search/results/recommended.json',BASE/'Lab6_limit_search/Lab6持续优化记录.md',BASE/'Lab4_optimized/adder_experiments/后续时序优化报告.md',Path('/home/ding/桌面/Lab/Lab项目Codex交接.md'),Path('/home/ding/桌面/Lab/Lab6架构优化试验记录.md')]
import shutil
for p in paths:shutil.copy2(p,context/p.name)
(OUT/'inventory.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
lines=['# 失败试验精简记录（2026-10-08）','','已确认失败的 7 组试验；不将取消/暂停、未验证或仅性能较差的方案混写成硬件失败。代表工程、原始课程数据、共享依赖及暂停中的 dual512_hybrid_full_lookup 保留。','','| 原工程相对路径 | 结论与依据 | 删除前占用 MiB | 保留记录 MiB |','| --- | --- | ---: | ---: |']
for e in entries:lines.append('| `'+str(Path(e['source']).relative_to(BASE))+'` | '+e['reason']+' | %.2f | %.2f |'%(e['allocated_bytes_before']/1024**2,e['archive_size']/1024**2))
lines+=['','每个 `.tar.gz` 仅保留源码、TB、配置、输入数据、结果 JSON、日志、文本报告和脚本；不包含 DCP、波形、综合数据库、IP生成文件和缓存。`inventory.json` 记录删除前每个文件的大小、SHA-256 和是否进入归档。归档已逐文件解包读取并核对原始 SHA-256。失败证据保留不能理解为可直接恢复原 DCP；如要重试，需要重建工程并重新综合/实现。','','历史数据以当前各项目 `results/run_status.json` 和实际错误日志为准，context 中旧汇总可能过期。Lab4 数值正确和 DSP 倍频理想仿真正确均不代表通过时序或上板。未重新运行仿真和实现。','','唯一外部源码引用是 `Lab6_limit_search/tools/count_carry.tcl` 的旧 `dual512_lookup/results/synth.dcp`；该历史分析脚本随 DCP 删除后不能直接运行，应查看归档中的综合资源报告，或重建失败版本。保留工程的 RTL、初始化数据、XPR 和运行脚本未发现引用本次删除目录的依赖。','','解压示例：`mkdir /path/to/restored-failed-trial && tar -xzf Lab6_limit_search__dual512_lookup.tar.gz -C /path/to/restored-failed-trial`。归档中的绝对路径沿用原环境，重跑前需检查路径。','','删除动作在本地归档校验、GitHub 上传及重新读取归档校验通过后执行；实际执行清单见 `cleanup_receipt.json`。']
(OUT/'README.md').write_text('\n'.join(lines)+'\n')
print('Total allocated MiB:',sum(e['allocated_bytes_before'] for e in entries)/1024**2,'record MiB:',sum(e['archive_size'] for e in entries)/1024**2)
