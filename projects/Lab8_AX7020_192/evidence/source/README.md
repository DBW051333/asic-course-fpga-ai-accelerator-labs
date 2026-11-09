# Lab8 192路综合优化工程

此工程整合此前已验证的有效优化，源基线为重新量化的 `lab8_128_resource_v1`，直接派生自 `fc2_192_single_acc`。功能RTL保持与该候选一致，仅调整数据文件路径；在本目录重新构建、仿真和导出部署文件。

## 已整合方案

| 方案 | 工程位置 | 作用 |
|---|---|---|
| FC1 192路全DSP、DSP流水精简 | rtl/core/fc1_paired.v | 保持192路规模，降低寄存器成本 |
| 171拍密集发射、双输入银行 | rtl/core/fc1_paired.v | 减少调度空拍，支持下一样本装载 |
| 批量DMA、跨样本流水 | rtl/lab8_npu.v、rtl/core/lab7_core.v | 核心216拍，批量启动间隔172拍 |
| FC1输入LUTRAM | rtl/core/fc1_paired.v | 降低输入缓存寄存器开销 |
| 加法树重定时 | rtl/core/adder_tree64.v | 精简流水寄存器并保持输出时刻 |
| FC2单套21位累加器 | rtl/core/fc_stream_pair_output.v | 保留DSP流水、结果快照和逐拍接口，降低FF |
| 单PL时钟 | tools/build.tcl | NPU/DMA/AXI共用142.857132 MHz，7 ns |

完整继承链及排除项见 `integration.json`，逐版RTL变化见 `evidence/lineage_rtl_changes.json`。双时钟试验、低收益提前启动与尚未集成的原型不纳入本工程。

## 打开和复现

Vivado 2025.2：打开 `vivado/Lab8.xpr`；构建目标为 PYNQ-Z2 / xc7z020clg400-1，PS preset 沿用 PYNQ-Z2，尚未适配AX7020。

在工程根目录执行：
```bash
python3 tools/verify_reference.py
python3 tools/run_sim.py axis
python3 tools/test_ps.py
python3 tools/check_boundaries.py
/vivado/2025.2/Vivado/bin/vivado -mode batch -source tools/build.tcl -tclargs all
python3 tools/run_dma_schedule.py
python3 tools/run_dma_sim.py
/vivado/2025.2/Vivado/bin/vivado -mode batch -source tools/verify_checkpoint.tcl
python3 tools/finalize_integration.py
```

工具链和板卡库路径按当前电脑配置。项目内权重路径为本目录绝对路径，整体迁移目录后须调整RTL/testbench路径并重新构建；部署包内PS程序和模型使用相对路径。

## 结果与部署

本次新构建结果以 `results/summary.json`、`timing_summary.rpt`、`checkpoint_verified.json` 为准；此前来源结果在 `evidence/source_summary.json`，不作为本次新布局布线结果。

部署入口：`deploy/lab8_integrated_192.tar.gz`。解压后 `lab8.bit/hwh/xsa` 来自本次同一完整构建，配套 `lab8_driver.py`、`run_lab8.py`、`run_batch.py`、`benchmark_api.py` 和模型输入文件。程序参数使用 `python3 run_lab8.py --help`、`python3 run_batch.py --help` 查看。

本次新跑集成RTL、标量参考、主机测试、协议边界、真实AMD DMA IP及完整布局布线；FC1极值/CE/对银行压力、FC2逐拍旧新等价证据复用功能一致的来源候选，详见summary。DMA采用仿真内存和理想PS事务，不能当作ARM/Python端到端耗时。未上板、未实测功耗；16383最大批量只检查协议/驱动边界。沿用PS DDR预设警告，PL时序通过不代表实际板上DDR验证。

原128/256基线、历史候选与 `当前192工程` 默认选择均保留。综合工程入口为工作区 `Lab8/整合优化工程`。

## 本次最终结果

| 资源 | 原批量集成版 | 综合优化版 | 减少率 |
|---|---:|---:|---:|
| lut | 19969 | 14328 | 28.25% |
| ff | 32608 | 18905 | 42.02% |
| slice | 9875 | 5993 | 39.31% |
| bram36_equivalent | 56 | 56 | 0.00% |
| dsp | 212 | 212 | 0.00% |

本目录完整新构建、保存DCP复核：WNS +0.015 ns，WHS +0.052 ns；216核心周期、172批量启动间隔、42样本DMA7423周期均保持一致。上述为仿真和布局布线结果。
