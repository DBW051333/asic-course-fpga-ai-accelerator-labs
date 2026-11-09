# AX7020 PS API v3 独立优化

工程 ID `lab8_ax7020_ps_api_v3`，直接父版 `lab8_ax7020_ps_api_v2`，源指定基线 `lab8_128_resource_v1`。
依据 2026-10-12 的 AX7020优化指南_v3.md，从 v2 保留全部输入路径及 DMA 完成优化，改善批量响应解析。

初始预算两个解析原型，主指标同板同轮 N=42 完整 API 中位数再降低至少 5%；其他 N 的中位数/P95 超过 5% 退化需调查。
补测解析交叉点后，正式对照之前固定规则：N<=48 使用 Struct('<BbbBI') 解码，N>48 使用小端 uint64 掩码合并非法类别和 padding 校验。
所有长度、signed score/class（平分为0）、padding、硬件字节计数和统计字段保留，输出为可写的独立副本。
四个硬件统计仍逐个读取当前值，DMA、模型、RTL、bit/hwh/XSA、时钟均与 v2 相同。本轮不运行 RTL 实现。

真实板端独立目录 `/home/xilinx/jupyter_notebooks/Lab8_AX7020_ps_api_v3`，运行 `Lab8_AX7020_ps_api_v3.ipynb`。
正式复现入口：在 PYNQ 环境运行 `board_suite.py`，会顺序执行 A/B、逐层回归、120秒持续测试与真实 DMA 故障恢复。先保存既有结果。
主机回归：`python tools/test_ps.py`（15项）及 `python tools/verify_reference.py`。

`ps/parent_driver.py` 是 v2 原样副本，`prototype1_driver.py` 是整字原型，`prototype2_driver.py` 是记录解码原型；最终候选为 `lab8_driver.py`。
`parse_microbench.py` 仅为无 DMA/MMIO 的解析归因，不用其结果代替完整 API 收益。固定整批预分配策略且两版相同；N>42 重复课程输入，不扩展准确率样本。

报告 `results/optimization_report.md`，原始数据 `results/board`，归档 `deploy/lab8_ax7020_ps_api_v3.tar.gz`。
部署保持 bit/hwh 同名；XSA 独立命名 `lab8_ax7020_192.xsa`。原双基线、父版与默认工程不切换。
历史 RTL 构建脚本保留作来源记录，绝对路径仍指向原硬件工程，本轮未运行。
