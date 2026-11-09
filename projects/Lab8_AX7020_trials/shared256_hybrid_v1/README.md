# AX7020 单 bank 256 路复用实验

实验ID `lab8_ax7020_shared256_hybrid_v1`，直接父版 `lab8_ax7020_shared192_v1`，原始来源 `lab8_128_resource_v1`。用户于2026-10-20授权从264周期复用版独立派生256路：220 DSP＋36路LUT打包乘法单元。原双基线、192复用版和默认工程均保留。512路本轮未实施。

完整工程目录 `hybrid256/`。硬件是三层共享乘法阵列与两棵归约树，FC1为256路/2组；FC2/FC3等待前层完成，继续使用同一阵列。输入、权重仍是原重新量化INT8，单样本CMD1推理与CMD2逐层读回；未接入批量CMD3。这里“36路LUT乘法”指36个软乘法单元，不是36个LUT查找表。

## LUT乘法器选择

公平比较36路、每路每拍一个打包任务、三拍乘法流水、相同输入/输出寄存器、相同CE、同一器件和7ns约束。资源包含符号处理、部分积、恢复和流水。表中时序仅为独立测试核内部寄存器路径，不代替整个NPU时序。

|36路测试核|LUT|FF|DSP|WNS ns|WHS ns|
|---|---:|---:|---:|---:|---:|
|通用signed25×signed8|6867|4680|0|+1.116|+0.036|
|24×8 radix-4 Booth/CARRY4|3780|6372|0|+2.082|+0.098|
|打包编码特化Booth，选用|2880|5292|0|+2.327|+0.098|

专用核LUT比通用实现减少58.06%，比24×8 Booth减少23.81%。完整阵列中，每个软乘法子模块综合为72 LUT/66 FF；测试核的每路80 LUT还包括动态打包接口相关逻辑，其资源口径与完整系统层级不同，不相加重复计算。最终完整系统指标见 `hybrid256/results/summary.json`（完成实现并审计后生成）。

打包系数 `B=65536*w1+w0`。B[15:8]重复w0符号位，Booth第4..7组恒为零。所选方案对B编码并跳过这些零部分积；高段首组保留B[15]作为前一Booth位，避免错误地把B[23:16]当作原始w1。实现见 `packed_mul.v`，资料和编码核查见同级实验 `../packed25x8_lut_research_v1/检索与编码核查.md`。

当前全部固定权重无损容纳于signed24。所有65536组INT8权重中，有128组不满足signed24；不能未经检查替换模型。本实验穷举其余65408组权重对×256个激活，共16744448组，并插入随机CE暂停，三方案均输出精确的两路signed16结果。激活保留完整signed8，不以课程样本小值较多缩减精度。

## 验证与指标口径

- 相同核心测试口径：192路父版264周期，本版200周期，约1.848→1.400 μs，延迟降低24.24%。FC1最后输出146周期、FC2最后输出180周期、FC3最后输出200周期。
- NPU软件可读compute计数包含封装启动计数，为201周期；不要与核心testbench的200周期混写。AXIS/AXI-Lite回归核对该计数。
- 核心48样本/7776逐层值通过；96样本压力测试15552逐层值、12288个FC1全精度值通过，含INT8极值、随机输入、2757个CE暂停和三层运行中的中断复位。
- AXIS/AXI-Lite回归48任务、42/42分类、7776逐层值通过。实际AMD AXI DMA IP仿真、布线后功能网表及完整系统实现的最终状态由 `hybrid256/results/` 内对应JSON与报告记录。
- Python驱动5项测试使用模拟传输；不会将它记录为DMA板测。新硬件未上板，未测实际API延迟或功耗。

## 复现

保留最终RTL和data直接重建，不需要运行初始搭建脚本。`prepare_kernels.py`、`prepare_full.py`、`prepare_system.py`是初始构建过程记录，会覆盖候选目录，不能作为最终增量构建入口。

```bash
# 36路核比较
python3 test_mul.py
/vivado/2025.2/Vivado/bin/vivado -mode batch -source build.tcl -tclargs "$PWD/kernels/packed_sparse" kernel
python3 summarize_kernels.py
# 三层核心/压力测试
python3 verify_core.py hybrid256
python3 verify_stress.py hybrid256
# 完整AX7020 PS/DMA/NPU，生成bit/hwh/XSA
/vivado/2025.2/Vivado/bin/vivado -mode batch -source hybrid256/tools/build.tcl
python3 hybrid256/tools/run_sim.py axis
python3 hybrid256/tools/run_dma_sim.py
# 独立核心实现与原生UNISIM布线后功能检查
/vivado/2025.2/Vivado/bin/vivado -mode batch -source build.tcl -tclargs "$PWD/hybrid256" core
python3 verify_mapped.py hybrid256
```

`baseline192`是父版源码及原布线证据的冻结副本，仅重写了本地读取路径。其DCP/报告继承原始构建，不能解释成新的192路综合、系统布线或板测。来源校验见 `baseline_identity.json`。
