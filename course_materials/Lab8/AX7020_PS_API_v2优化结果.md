# AX7020 PS API v2 优化结果

后续安排见[AX7020优化指南 v3](AX7020优化指南_v3.md)：以本软件候选为下一轮直接父版，优先分析响应解析/统计，使用新的同轮收益分母；默认工程选择保持不变。

2026-10-12，按第二版优化指南，从 ps_api_v1 独立派生 ps_api_v2，完成 DMA 等待/完成路径优化与真实 AX7020 验证。

| 完整 API 中位数 | 本轮 v1 | v2 | 降低 |
|---|---:|---:|---:|
| scalar 单样本 | 1.179 ms | 0.969 ms | 17.82% |
| batch N=42 | 1.760 ms | 1.596 ms | 9.29% |
| batch N=128 | 1.988 ms | 1.827 ms | 8.10% |

N=42 的 P95 降低 8.65%。同一 Overlay，A/B/B/A/A/B/B/A，每版每个测点 400 次；本轮收益相对于 v1，不重复计算 v1 历史收益。

实板分类 42/42 正确、6804 逐层特征相符。120 秒持续运行 31784 批事务、3228862 次重复课程样本输入，硬件错误 0；真实 DMA 超时、长度错误、自动复位及后续完整批量推理恢复均通过。

保留 PYNQ transfer、缓存同步、实际字节数、输入/响应检查与结果副本寿命。硬件和模型完全复用：FC1 192 路，DSP 212，单 PL 时钟约 142.857 MHz；未重新布局布线。指定基线、父版及默认工程未切换。

- [完整报告](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v2/results/optimization_report.md)
- [独立工程](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v2/README.md)
- [正式原始 A/B](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v2/results/board/comparison.json)
- [真实 DMA 故障记录](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v2/results/board/dma_fault_results.json)
- [部署包](/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v2/deploy/lab8_ax7020_ps_api_v2.tar.gz)
- [板端 Notebook](http://192.168.2.99:9090/notebooks/Lab8_AX7020_ps_api_v2/Lab8_AX7020_ps_api_v2.ipynb)

板端独立路径 `/home/xilinx/jupyter_notebooks/Lab8_AX7020_ps_api_v2`；包与板端文件哈希核验见完整报告的校验记录。
