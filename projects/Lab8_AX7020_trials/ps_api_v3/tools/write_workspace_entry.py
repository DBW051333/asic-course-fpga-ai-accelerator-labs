"""Publish local navigation only after new board and package verification."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];W=Path('/home/ding/桌面/Lab/Lab8')
s=json.loads((R/'results/optimization_summary.json').read_text());d=json.loads((R/'results/deployment_verified.json').read_text());assert s['pass'] and d['pass']
entry=W/'AX7020软件优化v3工程';assert not entry.exists() or entry.resolve()==R
if not entry.exists():entry.symlink_to(R,target_is_directory=True)
lines=['# AX7020 PS API v3 优化结果','','2026-10-12，按第三版优化指南，从 ps_api_v2 独立派生，完成批量响应解析优化和真实 AX7020 验证。','', '| 完整 API 中位数 | 本轮 v2 | v3 | 降低 |','|---|---:|---:|---:|']
for item in s['api_results']:
 if item['mode']=='batch' and item['N'] in [42,128,256,512]:
  a=item['variants']['A']['stats']['api_wall_us']['median']/1000;b=item['variants']['B']['stats']['api_wall_us']['median']/1000
  lines.append(f"| batch N={item['N']} | {a:.3f} ms | {b:.3f} ms | {item['api_median_reduction_percent']:.2f}% |")
lines+=['',f"N42 的 P95 降低 {s['primary_p95_reduction_percent']:.2f}%。正式 A/B 共14个测点，每版每点400次，按 A/B/B/A/A/B/B/A 轮换；收益相对同轮 v2，不叠加历史收益。",'', 'N≤48 使用固定记录 signed 解码，N>48 使用整字合并校验；两分支均保留完整响应验证和可写结果快照。scalar 路径、DMA、四个硬件统计读取和 PL 硬件均保持原样。', '', f"实板42/42分类正确，6804个逐层值一致；120秒完成{s['stress']['transactions']}批事务、{s['stress']['samples']}次重复课程输入，硬件错误0。真实 DMA 超时与长度错误自动复位恢复重新验证通过。主机15项回归通过。", '', 'FC1 192路全DSP，DSP212，约142.857MHz单PL时钟。原父版、指定双基线、默认AX7020工程均保留。', '', f'- [完整报告]({R}/results/optimization_report.md)', f'- [工程说明]({R}/README.md)', f'- [正式原始 A/B]({R}/results/board/comparison.json)', f'- [持续测试]({R}/results/board/stress_results.json)', f'- [部署包]({R}/deploy/lab8_ax7020_ps_api_v3.tar.gz)', f'- [包与板端核验]({R}/results/deployment_verified.json)', '- [板端Notebook](http://192.168.2.99:9090/notebooks/Lab8_AX7020_ps_api_v3/Lab8_AX7020_ps_api_v3.ipynb)', '', '板端独立目录 `/home/xilinx/jupyter_notebooks/Lab8_AX7020_ps_api_v3`。未测功耗、断电冷启动或长期可靠性；完整范围见报告。','']
(W/'AX7020_PS_API_v3优化结果.md').write_text('\n'.join(lines))
p=W.parent/'README_资料索引.md';v=p.read_text();old='Lab8 AX7020 最新软件优化：[PS API v2 优化结果](Lab8/AX7020_PS_API_v2优化结果.md)（2026-10-12，相对 v1 同板42批量 API 时间再减少9.29%，真实板测与 DMA 故障恢复通过）。';new=f"Lab8 AX7020 最新软件优化：[PS API v3 优化结果](Lab8/AX7020_PS_API_v3优化结果.md)（2026-10-12，相对 v2 同板42批量 API 再减少{s['primary_api_median_reduction_percent']:.2f}%，14点正式 A/B、持续板测与 DMA 故障恢复通过）。\n\n上一轮结果：[PS API v2](Lab8/AX7020_PS_API_v2优化结果.md)。";assert old in v;p.write_text(v.replace(old,new))
print('Workspace v3 entry and index updated; default selection preserved')
