# AX7020 PS API v3 优化结果

2026-10-12，按第三版优化指南，从 ps_api_v2 独立派生，完成批量响应解析优化和真实 AX7020 验证。

| 完整 API 中位数 | 本轮 v2 | v3 | 降低 |
|---|---:|---:|---:|
| batch N=42 | 1.588 ms | 1.378 ms | 13.21% |
| batch N=128 | 1.821 ms | 1.703 ms | 6.47% |
| batch N=256 | 2.186 ms | 2.052 ms | 6.13% |
| batch N=512 | 2.912 ms | 2.743 ms | 5.82% |

N42 的 P95 降低 11.82%。正式 A/B 共14个测点，每版每点400次，按 A/B/B/A/A/B/B/A 轮换；收益相对同轮 v2，不叠加历史收益。

N≤48 使用固定记录 signed 解码，N>48 使用整字合并校验；两分支均保留完整响应验证和可写结果快照。scalar 路径、DMA、四个硬件统计读取和 PL 硬件均保持原样。

实板42/42分类正确，6804个逐层值一致；120秒完成33449批事务、3398008次重复课程输入，硬件错误0。真实 DMA 超时与长度错误自动复位恢复重新验证通过。主机15项回归通过。

FC1 192路全DSP，DSP212，约142.857MHz单PL时钟。原父版、指定双基线、默认AX7020工程均保留。

- [完整报告](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v3/results/optimization_report.md)
- [工程说明](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v3/README.md)
- [正式原始 A/B](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v3/results/board/comparison.json)
- [持续测试](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v3/results/board/stress_results.json)
- [部署包](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v3/deploy/lab8_ax7020_ps_api_v3.tar.gz)
- [包与板端核验](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v3/results/deployment_verified.json)
- [板端Notebook](http://192.168.2.99:9090/notebooks/Lab8_AX7020_ps_api_v3/Lab8_AX7020_ps_api_v3.ipynb)

板端独立目录 `/home/xilinx/jupyter_notebooks/Lab8_AX7020_ps_api_v3`。未测功耗、断电冷启动或长期可靠性；完整范围见报告。
