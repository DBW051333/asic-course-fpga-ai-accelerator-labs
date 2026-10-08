from pathlib import Path
import sys,json,re
sys.path.insert(0,'/home/ding/vivado_project/Lab6_limit_search/tools')
from collect import resources,row
R=Path('/home/ding/vivado_project/Lab6_three_version_comparison');D=R/'original_int8';r=D/'results'
log=(r/'final_verify_console.log').read_text(errors='replace');m=re.search(r'PERFORMANCE latency_cycles=(\d+)\.\.(\d+)',log);a,b=map(int,m.groups());assert a==b
m=re.search(r'INTERVAL cycles=(\d+)\.\.(\d+) latency=(\d+)\.\.(\d+)',log);i,j,c,d=map(int,m.groups());assert i==j and c==d==a
x={'name':'Lab6 原版8位','project':'/home/ding/vivado_project/Lab6/vivado8/Lab6_8.xpr','cycles':a,'interval_cycles':i,**resources(r/'utilization_impl.rpt'),**json.loads((r/'final_clock.json').read_text())}
s=(r/'timing_final.rpt').read_text();m=re.search(r'WNS\(ns\).*?\n\s*-+.*?\n\s*([^\n]+)',s,re.S);v=m[1].split();assert float(v[0])>=0 and float(v[1])==0 and float(v[4])>=0 and float(v[5])==0 and float(v[8])>=0 and float(v[9])==0
m=re.search(r'# of nets with routing errors\.*\s*:\s*(\d+)',(r/'route_status.rpt').read_text());assert int(m[1])==0
x['timing_pass']=True;x['route_errors']=0;x['accuracy']='37/42'
x['latency_ns']=round(a*x['period'],2);x['interval_ns']=round(i*x['period'],2)
rows=[x,row(Path('/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11')),row(Path('/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual'))]
for x in rows:
 x['frequency_mhz']=round(1000/x['period'],2);x['throughput_m_per_s']=round(1000/x['interval_ns'],3);x['latency_speedup_vs_original']=round(rows[0]['latency_ns']/x['latency_ns'],2)
(R/'comparison.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
metrics=[('LUT 个','lut',lambda v:f'{int(v):,}'),('寄存器 FF 个','ff',lambda v:f'{int(v):,}'),('BRAM 36Kb块','bram',lambda v:f'{v:g}'),('DSP 个','dsp',lambda v:str(int(v))),('通过时序检查的周期 ns','period',lambda v:f'{v:.2f}'),('对应频率 MHz','frequency_mhz',lambda v:f'{v:.2f}'),('单次计算周期数','cycles',str),('单次计算延迟 ns','latency_ns',lambda v:f'{v:,.2f}'),('连续任务启动间隔 拍','interval_cycles',str),('连续任务启动间隔 ns','interval_ns',lambda v:f'{v:,.2f}'),('连续任务吞吐率 百万次每秒','throughput_m_per_s',lambda v:f'{v:.3f}'),('单次计算速度 相对原版','latency_speedup_vs_original',lambda v:f'{v:.2f}×')]
lines=['# Lab6 原版与两个优化版本对比','','| 指标 | Lab6 原版 8 位 | 资源较省优化版 | 高并行特色版 |','|---|---:|---:|---:|']
for title,key,fmt in metrics:lines.append('| '+title+' | '+' | '.join(fmt(x[key]) for x in rows)+' |')
lines+=['| 42个样本分类准确率 | 37/42（88.10%） | 37/42（88.10%） | 37/42（88.10%） |','| 数值校验和时序检查 | 通过 | 通过 | 通过 |','','比较口径：同为 xc7z020clg400-1，INT8 权重及层输出，截位规则为右移10/9/8后保留8位；42样本的三层共6804项参考输出完全一致。资源为布局布线后的 Vivado report_utilization，全网计算核心采用少量端口包装器，原版外部1024位写入端口固定为不写入，使用已有输入ROM初始化数据，避免将板级输入接口宽度计入比较；两个优化版也采用预加载输入方式。单次计算延迟从接收 start 的时钟沿到 done 有效，不包括外部加载数据和复位时间。原版连续启动间隔用同一输入连续3次启动实测；优化版用48组连续任务实测。吞吐率按1/启动间隔计算，表示内部计算吞吐率，不包含外部传输。','','时钟周期是各自本次布局布线满足 setup、hold、脉宽的约束周期，对应频率不是板上测得的频率，也不是对全部布局策略搜索得到的绝对最高频率。本表统一使用单周期时序约束，没有为原版设置多周期路径例外；原版控制器有多拍等待，因此这里的原版周期是保守口径，不能据此断言原版在正确多周期约束下也只能达到这个频率。BRAM按36Kb块统计，半块代表18Kb。所有实现均零布线错误，保存的 DCP 重开复核通过。原版最终周期下42样本功能校验通过，优化版各48组7776项数值/地址校验通过；未上板。','','工程与证据：',f'- 原版课程工程：[Lab6_8.xpr](/home/ding/vivado_project/Lab6/vivado8/Lab6_8.xpr)。此次独立测量保存在 [{D}]({D})，原课程工程没有覆盖。','- 资源较省版：[fc2_interleaved_split11](/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11)。','- 高并行特色版：[fc1_128x6_dual](/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual)。',f'- 原版测量脚本：[run_synth.tcl]({D}/tools/run_synth.tcl)、[run_impl.tcl]({D}/tools/run_impl.tcl)、[run_final_verify.tcl]({D}/tools/run_final_verify.tcl)。各版 results 目录保留 utilization_impl.rpt、timing_final.rpt、final_clock.json、final_verify_console.log、route_status.rpt。',f'- 机器可读数据：[comparison.json]({R}/comparison.json)。']
p=Path('/home/ding/桌面/Lab/Lab6三个版本资源与性能对比.md');p.write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:18]))
