from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];W=Path('/home/ding/桌面/Lab/Lab8')
s=json.loads((R/'results/optimization_summary.json').read_text());d=json.loads((R/'results/deployment_verified.json').read_text());assert s['pass'] and d['pass']
entry=W/'AX7020平台优化v1工程';assert not entry.exists() or entry.resolve()==R
if not entry.exists():entry.symlink_to(R,target_is_directory=True)
lines=['# AX7020 平台优化 v1 实板结果','','2026-10-12，从PS API v3独立派生，NPU/DMA/PL AXI统一166.667MHz，FC1保持192路、DSP212、模型不变。','', '|完整API|同轮v3|平台v1|中位数减少|','|---|---:|---:|---:|']
for v in s['api_results']:
 if v['mode']=='batch':
  lines.append(f"|N={v['N']}|{v['variants']['A']['stats']['api_wall_us']['median']/1000:.3f} ms|{v['variants']['B']['stats']['api_wall_us']['median']/1000:.3f} ms|{v['api_median_reduction_percent']:.2f}%|")
lines+=['', 'PL时间减少14.29%，理想吞吐提高16.67%；N2048/4096完整API达到至少5%目标，N42无测得收益。8块交替A/B，每点每版400次。WNS +0.049ns、WHS +0.050ns。', '', f"实板42/42正确、6804逐层特征一致；120秒{s['stress']['transactions']}个事务、{s['stress']['samples']}次重复样本，0错误。真实DMA超时及长度错误恢复通过。", '', 'ARM仍666.7MHz，DDR仍533.3MHz。ARM767MHz只生成离线PS配置XSA，未部署；DDR方向经事务周期分析暂缓，不能宣称DDR已调优。未尝试200MHz。', '', '默认current_project.json与双基线/父版均保留。板端最后装载平台v1，原启动文件未改。', '', f'- [完整报告]({R}/results/optimization_report.md)', f'- [原始A/B]({R}/results/board/comparison.json)', f'- [部署包]({R}/deploy/lab8_ax7020_platform_v1.tar.gz)', f'- [板端包校验]({R}/results/deployment_verified.json)', '- [板端Notebook](http://192.168.2.99:9090/notebooks/Lab8_AX7020_platform_v1/Lab8_AX7020_platform_v1.ipynb)', '']
(W/'AX7020平台优化v1结果.md').write_text('\n'.join(lines))
p=W.parent/'README_资料索引.md';v=p.read_text();line='Lab8 AX7020 最新平台实验：[平台优化 v1 实板结果](Lab8/AX7020平台优化v1结果.md)（2026-10-12，统一166.667MHz；相对同轮PS API v3，N4096完整API减少5.67%，N42无测得收益；默认工程未切换）。\n\n';v=v.replace('# Lab资料索引\n','# Lab资料索引\n')
if line not in v:v=line+v
p.write_text(v)
print('Workspace platform entry and index updated')
