# AX7020 Lab8 PS API优化结果

后续安排见[AX7020优化指南 v2](AX7020优化指南_v2.md)（2026-10-12）：以本候选为下一轮软件实验对照，优先剖析响应解析/统计与DMA调用，默认工程选择保持不变。

2026-10-12，根据AX7020最新优化指南完成软件路径优化并自行上板验收。独立工程ID `lab8_ax7020_ps_api_v1`，直接父版 `lab8_ax7020_192`，源指定基线 `lab8_128_resource_v1`。

| 完整API中位数 | 同轮父版 | 优化版 | 时间减少 |
|---|---:|---:|---:|
| 单样本scalar | 1.762 ms | 1.167 ms | 33.80% |
| batch N=42 | 3.313 ms | 1.750 ms | 47.18% |
| batch N=128 | 4.830 ms | 1.981 ms | 58.97% |

每版每个规模测400次，按A/B/B/A/A/B/B/A顺序轮换；全部测点P95均改善。原型依据、分段时间、计时边界与全部原始结果均保留。

优化int8合法输入检查、转换/打包与缓冲区数据访问；保留校验、cache同步、超时、错误恢复和返回结果生命周期。模型、bit/hwh、RTL、192路全DSP和PL共享时钟保持原样；此次没有新布局布线或硬件资源收益。

真实AX7020通过42/42分类、6804逐层值、连续批量、异常/复位/重载恢复，另120秒30332批量事务、3081531重复负载样本、98172额外特征值检查，硬件错误0；规模覆盖到512。未测功耗、全DDR压力或完整16383批量。

- [完整优化与板测报告](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v1/results/optimization_report.md)
- [工程说明](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v1/README.md)
- [A/B原始数据](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v1/results/board/comparison.json)
- [连续板测原始数据](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v1/results/board/stress_results.json)
- [部署包](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v1/deploy/lab8_ax7020_ps_api_v1.tar.gz)
- [板上Notebook](http://192.168.2.99:9090/notebooks/Lab8_AX7020_ps_api_v1/Lab8_AX7020_ps_api_v1.ipynb)

原AX7020父版与128/256基线保护校验通过，当前选择文件继续保留父版；新的已部署优化入口是本页独立版本。
