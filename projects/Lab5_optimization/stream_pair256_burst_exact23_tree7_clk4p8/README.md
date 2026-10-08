# Lab5 最终优化工程

三层独立计算，精确整数运算，借鉴 Lab4 的单累加器与流水加法树，并增加跨层流式计算、DSP 双乘积打包、逻辑部分积流水线及 FC2 结果快照。

| 指标 | 最终结果 |
|---|---:|
| 单次完整网络 | 168 周期 / 0.88368 μs |
| 连续请求启动间隔 | 129 周期 / 0.67854 μs |
| 内部布线复核时钟 | 5.26 ns |
| LUT / FF | 23944 / 41984 |
| BRAM Tile / DSP | 61 / 216 |
| Setup / Hold 最差余量 | +0.005 ns / +0.050 ns |

原始基准为 1834 周期、100 MHz 下 18.34 μs，原始 288 DSP 超过器件容量。

## 打开与复核

- 源工程：`vivado/stream_pair256_burst_exact23_tree7_clk4p8.xpr`。
- 最终物理状态：`results/final_routed.dcp`，包含 5.26 ns 时钟；直接打开该文件查看最终通过的时序。
- `timing.xdc` 的 4.8 ns 是布局优化目标。最终经过完整复核通过的周期为 5.26 ns，报告见 `results/timing_final.rpt`。
- 在本目录运行 `vivado -mode batch -source tools/verify_final.tcl`，重新读取最终 DCP 并报告时序、资源。
- 从源代码重现：依次执行 `tools/create_sim.tcl`、`tools/run_serial_impl.tcl`、`tools/run_explore.tcl`。Explore 脚本保存 `results/explore_routed.dcp` 和 `results/timing_explore_final.rpt`。

## 接口与功能

物理顶层 `lab5_impl_top` 输出最终 64 位结果。`ready_o` 为高时，可以用单拍 `start_i` 发起下一次计算；`done_o` 每完成一组两个结果产生一拍。一次计算未完成时允许发起下一次请求，按 ready 接收。

仿真顶层 `lab5_top` 保留三层调试输出。FC2 每拍提供四个相邻结果 `fc2_data_o`、`fc2_data_b_o`、`fc2_data_c_o`、`fc2_data_d_o`；地址表示首个结果。32/48/64 位结果接口保持精确值。需要原 FC2 单输出接口时，可使用对照工程 `stream_pair256_partial5_clk5`，188 周期、5.42 ns、约 1.019 μs。

三次连续课程输入全部 486 个值与地址一致；六组不同输入的串行及重叠计算全部 972 个值与地址一致，最终时钟验证日志见 `results/validation_final_clock.log`、`results/burst_final_clock.log`。

公共系数和初始化输入位于 `/home/ding/vivado_project/Lab5_optimization/data`。输入沿用课程初始化 ROM，综合默认课程输入；行为仿真通过更新 ROM 验证不同输入。更改权重后应重新计算位宽界限。

内部时序与行为仿真已验证，外部 IO 时序和板上实测尚未包含。

详细对照报告：[Lab5三层网络优化报告](/home/ding/vivado_project/Lab5_optimization/Lab5三层网络优化报告.md)。
