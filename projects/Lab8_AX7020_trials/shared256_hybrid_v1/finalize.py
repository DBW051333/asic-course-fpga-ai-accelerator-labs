from pathlib import Path
import json,re,hashlib,shutil,tarfile
R=Path(__file__).resolve().parent;D=R/'hybrid256';P=D/'results'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def util(f):
 s=f.read_text();o={}
 for key,label in [('lut','Slice LUTs'),('ff','Slice Registers'),('bram36_equivalent','Block RAM Tile'),('dsp','DSPs')]:
  o[key]=float(re.search(r'\| '+label+r'\s*\|\s*([0-9.]+)',s).group(1))
 return o
def timing(f):
 s=f.read_text();return {k:float(re.search(label+r'\s+(-?[0-9.]+)',s).group(1)) for k,label in [('wns_ns','Setup WNS'),('whs_ns','Hold WHS')]}
b=json.loads((R/'baseline_identity.json').read_text());origin=Path(b['direct_source'])
assert all(sha(origin/n)==h for n,h in b['source_sha256'].items()),'parent changed'
checks={n:json.loads((P/(n+'.json')).read_text()) for n in ['core_verification','stress_verification','simulation_axis','simulation_dma','python_tests','mapped_verification','dsp_audit','final_checkpoint_audit','model_verification']}
assert all(x['pass'] for x in checks.values())
assert 'PASS 16744448 triples plus randomized CE stalls' in (R/'mul_test/result.log').read_text()
core=util(P/'routed_utilization.rpt');t=dict(x.split(maxsplit=1) for x in (P/'routed_metrics.txt').read_text().splitlines())
core.update(wns_ns=float(t['max']),whs_ns=float(t['min']),unrouted=int(t['UNROUTED']),route_errors=int(t['ROUTE_ERRORS']),core_cycles=200)
assert core['dsp']==220 and core['wns_ns']>=0 and core['whs_ns']>=0 and core['unrouted']==0 and core['route_errors']==0
sys=util(P/'utilization.rpt');sys.update(timing(P/'build_complete.txt'))
assert sys['dsp']==220 and sys['wns_ns']>=0 and sys['whs_ns']>=0
for n in ['lab8.bit','lab8.hwh','lab8_ax7020_shared256.xsa']:assert (D/'overlay'/n).stat().st_size>0
# Source and data identity; packaged build consumes exactly these final files.
sourcefiles=[f for sub in ['rtl','data','tools','tb','ps'] for f in (D/sub).rglob('*') if f.is_file() and '__pycache__' not in str(f)]
manifest={str(f.relative_to(D)):sha(f) for f in sourcefiles};(P/'source_sha256.json').write_text(json.dumps(manifest,indent=2))
artifacts={str(f.relative_to(D)):sha(f) for f in (D/'overlay').iterdir() if f.is_file()}
summary={'id':'lab8_ax7020_shared256_hybrid_v1','direct_parent':b['id'],'source_baseline':'lab8_128_resource_v1','part':'xc7z020clg400-2','nominal_clock_hz':142857132,'clock_ns':7,'selected_multiplier':'packed_sparse','architecture':{'packed_lanes':256,'dsp_lanes':220,'lut_packed_units':36,'fc1_groups':2,'single_bank':True,'layers_share_array':True,'commands':[1,2]},'ooc_core':core,'full_system':sys,'same_checker_parent':{k:b[k] for k in ['core_cycles','lut','ff','bram36','dsp']},'core_latency_reduction_percent':100*(264-200)/264,'core_time_us':1.4,'wrapper_compute_counter_cycles':201,'verification':checks,'board_tested':False,'board_latency_measured':False,'power_measured':False,'artifacts_sha256':artifacts,'parent_source_unchanged':True,'default_project_changed':False,'scopes':{'ooc':'internal register-to-register implementation; external core inputs/outputs lack system constraints','system':'full AX7020 PS7/DMA/interconnect/NPU timing implementation and bitstream; not a new board measurement','mapped':'post-route functional UNISIM, without SDF timing delays','dma':'actual AMD AXI DMA IP, RTL NPU, simulated DDR and AXI-Lite PS transactions'}}
(P/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
report=f'''# 256路复用完整版本结果\n\n选用打包编码特化Booth。220 DSP＋36路LUT软乘法，FC1为256路/2组，三层共用同一阵列和两棵加法树。INT8模型与逐层数值不变。\n\n## 同口径核心对比\n\n|指标|192路复用父版|256路复用本版|\n|---|---:|---:|\n|核心周期|264|200|\n|7ns下核心时间 μs|1.848|1.400|\n|LUT|9057|{int(core['lut'])}|\n|FF|22203|{int(core['ff'])}|\n|BRAM36|72|{core['bram36_equivalent']:g}|\n|DSP|192|220|\n|WNS ns|+0.017|{core['wns_ns']:+.3f}|\n|WHS ns|+0.114|{core['whs_ns']:+.3f}|\n\n延迟减少24.24%，持续纯计算服务率理论增加32%；实际API吞吐未板测。LUT增加{100*(core['lut']/9057-1):.2f}%，FF增加{100*(core['ff']/22203-1):.2f}%，BRAM增加24，DSP增加28。专用乘法器解决的是36路补充乘法的成本，并不意味着整个256路版本比192路更省资源。父版为继承的原OOC结果，不与本版全系统资源混用。\n\n## 完整AX7020系统\n\nPS7＋AXI DMA＋互连＋NPU：LUT {int(sys['lut'])}，FF {int(sys['ff'])}，BRAM36等效 {sys['bram36_equivalent']:g}，DSP {int(sys['dsp'])}；WNS {sys['wns_ns']:+.3f} ns，WHS {sys['whs_ns']:+.3f} ns。7 ns目标通过，bit/hwh/XSA来自同一最终实现。\n\n## 验证\n\n三种LUT核16744448组穷举及CE暂停通过；48样本7776逐层值、96输入15552逐层值和12288个FC1全精度值通过。压力测试含极值、随机输入、2757个CE暂停及三层中断复位。AXIS/AXI-Lite 48任务、42/42分类通过；真实AMD DMA IP仿真42样本6804逐层值通过，包含无历史和坏包回复、长度/字节边界检查。布线后功能网表8样本1296值通过。Python5项测试为模拟传输，不是板测。所有220 DSP处于MULTIPLY模式，软乘法模块DSP为0。\n\n核心testbench为200周期；封装compute寄存器包括启动计数，为201周期。两种计数起止口径不同。当前权重24位合法性已全部检查；更换权重必须重检。新版本未上板、未测功耗与实际API耗时；默认工程未切换。512路未实现。\n\n部署与重建入口见 `hybrid256/README.md`，明细与SHA256见 `hybrid256/results/summary.json`、`source_sha256.json`。\n'''
(R/'实验结果.md').write_text(report)
# Small deployment package: bit/hwh same basename; XSA deliberately has a different basename for PYNQ.
package=R/'deploy/lab8_ax7020_shared256';package.mkdir(parents=True,exist_ok=True)
for sub in ['ps','overlay']:
 for f in (D/sub).iterdir():
  if f.is_file():shutil.copy2(f,package/f.name)
for f in [D/'README.md',R/'实验结果.md',P/'summary.json',P/'source_sha256.json']:
 shutil.copy2(f,package/f.name)
(package/'sha256.json').write_text(json.dumps({f.name:sha(f) for f in package.iterdir() if f.is_file() and f.name!='sha256.json'},indent=2))
with tarfile.open(R/'deploy/lab8_ax7020_shared256.tar.gz','w:gz') as t:t.add(package,arcname=package.name)
branch={'baseline_id':b['id'],'baseline_path':str(R/'baseline192'),'baseline_original_path':b['direct_source'],'active_experiment':summary['id'],'active_experiment_path':str(D),'result_summary':str(P/'summary.json'),'status':'implemented_and_simulated_not_board_tested','default_current_project_unchanged':True}
Path('/home/ding/vivado_project/Lab8_baselines/shared_branch.json').write_text(json.dumps(branch,indent=2))
print(json.dumps({'core':core,'system':sys,'verification_pass':True,'deploy':str(R/'deploy/lab8_ax7020_shared256.tar.gz')},indent=2))
