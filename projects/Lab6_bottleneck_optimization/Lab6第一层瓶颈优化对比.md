# Lab6 第一层瓶颈优化记录

本轮以 Lab5 最佳版本延伸出的 Lab6 标准 8 位逐层截位方案为基线。独立 `/home/ding/vivado_project/Lab6` 工程未修改。目标是尽快改善单次计算时间，保留 8 位截位数值和所有层输出接口。

## 结论

本轮推荐 **postroute_fanout**。已布线通过周期 **4.74 ns**，单次 **801.06 ns**，相对上一轮 851.76 ns 减少 **5.95%**，相对原最佳未截位 Lab5 的 883.68 ns 减少 **9.35%**。分类仍为 37/42，最终时钟参数下 48 次重叠请求、7,776 个层输出和地址均通过检查。

## 抓住的主要瓶颈

上一轮关键路径从 FC1 地址寄存器，经两级 LUT 到 BRAM 使能端。4.437 ns 数据路径中布线占 3.733 ns（84.1%）；其中一个译码网络扇出为 115。因此优先处理终止地址译码和已有布局的物理优化，没有继续搜索量化位置，也没有扩大乘法器并行度。

## 小范围试验

- `postroute_fanout`：打开上一轮已布线 DCP，恢复 4.8 ns 目标，执行 AggressiveFanoutOpt 物理优化并重新布线。实际日志包含关键地址寄存器的时钟偏斜调整，因此收益属于物理优化与重新布线组合，不能归因于单独降低扇出。RTL 与原方案一致。
- `terminal_tree8`：第一层末地址判断提前一拍寄存，并将地址位宽收紧到合法范围所需的 7 位；保留 8 级加法树，无新增拍数。各阶段状态见下表；实现流程包含布线后物理优化。
- `terminal_tree7`：同样修改控制逻辑，保留 7 级加法树。完成行为验证；本轮为控制试验数量和耗时，不进行该版本综合、布线，不宣称其硬件速度。

| 方案 | 仿真 | 综合 | 布线 | 拍数 | 周期 ns | 单次 ns | 启动间隔 ns | LUT | FF | BRAM | DSP |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| previous_best | passed | passed | passed | 169 | 5.04 | 851.76 | 650.16 | 20075.0 | 40600.0 | 61.0 | 220.0 |
| terminal_tree8 | passed | passed | passed | 169 | 4.9 | 828.1 | 632.1 | 20129.0 | 40653.0 | 61.0 | 220.0 |
| terminal_tree7 | passed | not_run | not_run | 168 | — | — | — | — | — | — | — |
| postroute_fanout | passed | not_run | passed | 169 | 4.74 | 801.06 | 611.46 | 20075.0 | 40600.0 | 61.0 | 220.0 |

控制逻辑改版最终为 4.90 ns、828.10 ns，相对上一轮减少 2.78%；但多用 54 LUT 和 53 FF，速度也未超过物理优化版本，因此不作为推荐。该改版的新关键路径为 running 寄存器到 BRAM 地址端，仍有约 82.7% 的数据路径延迟来自布线。推荐版本的关键路径转为 BRAM 读出到流水线寄存器，后续优先检查存储器输出寄存和布局。

## 验证与比较口径

所有改版沿用原始权重、偏置、8 位移位 10/9/8 和标签约定。42 个课程样本与 6 个扩展输入通过行为测试，逐层数值和地址对参考输出验证。物理优化版本沿用原 RTL，导出工程按最终周期重新仿真；这属于 RTL 功能验证，不是门级带延迟仿真。
每个完成布线的方案均报告 setup、hold、pulse width、完整布线和边界周期；通过周期在固定布线结果上按 0.01 ns 步长选择，并非保证的全局最高频率。推荐方案已重新打开保存的 DCP 再次核对时序、布线，并重新运行最终时钟参数下的仿真。
内部时钟路径通过，外部 IO 延迟和板级引脚仍未定义；未做板上实测。初始化输入 ROM 使用与上一轮一致的课程样本 1；更改物理 ROM 初始化后应重新综合及布线。
综合时同时运行物理优化导致内存压力，terminal_tree8 综合耗时不能作为线程性能比较。随后布线重任务串行执行。

## 交付与复现

- [推荐 Vivado 工程](/home/ding/vivado_project/Lab6_bottleneck_optimization/recommended/Lab6_bottleneck_recommended.xpr)
- [推荐已布线 DCP](/home/ding/vivado_project/Lab6_bottleneck_optimization/postroute_fanout/results/final_routed.dcp)
- [选中方案实现脚本](/home/ding/vivado_project/Lab6_bottleneck_optimization/postroute_fanout/tools/run_impl.tcl)
- [对比 CSV](/home/ding/vivado_project/Lab6_bottleneck_optimization/results/comparison.csv)
- [完整对比 JSON](/home/ding/vivado_project/Lab6_bottleneck_optimization/results/comparison.json)
- [最终复核日志](/home/ding/vivado_project/Lab6_bottleneck_optimization/results/final_verification_console.log)

推荐工程包含选中版本 RTL、参考数据、测试平台和最终时钟约束。若选中物理优化版本，测得的周期对应保存的已布线 DCP；从源码重新 Run All 不保证得到同一个布局或同一个周期。其实现脚本从上一轮已布线 DCP 开始，完整保留本轮优化过程。

## 后续有依据的方向

本轮另外根据固定权重对所有独立 INT8 输入及累加前缀计算范围：FC2 为 [-874237, 875063]，21 位足够；FC3 为 [-251408, 252217]，19 位足够。当前分别为 23、21 位。范围记录见 `results/fixed_weight_width_bounds.json`，本轮未修改这两层累加器；是否加速须继续布线验证。优先根据推荐方案的新关键路径决定下一步，避免仅凭资源减少判断加速。
