# Lab6 原版与两个优化版本对比

| 指标 | Lab6 原版 8 位 | 资源较省优化版 | 高并行特色版 |
|---|---:|---:|---:|
| LUT 个 | 6,271 | 15,782 | 35,323 |
| 寄存器 FF 个 | 10,250 | 37,767 | 71,269 |
| BRAM 36Kb块 | 46.5 | 68 | 103.5 |
| DSP 个 | 192 | 220 | 220 |
| 通过时序检查的周期 ns | 13.03 | 4.09 | 4.91 |
| 对应频率 MHz | 76.75 | 244.50 | 203.67 |
| 单次计算周期数 | 1834 | 174 | 135 |
| 单次计算延迟 ns | 23,897.02 | 711.66 | 662.85 |
| 连续任务启动间隔 拍 | 1835 | 129 | 89 |
| 连续任务启动间隔 ns | 23,910.05 | 527.61 | 436.99 |
| 连续任务吞吐率 百万次每秒 | 0.042 | 1.895 | 2.288 |
| 单次计算速度 相对原版 | 1.00× | 33.58× | 36.05× |
| 42个样本分类准确率 | 37/42（88.10%） | 37/42（88.10%） | 37/42（88.10%） |
| 数值校验和时序检查 | 通过 | 通过 | 通过 |

比较口径：同为 xc7z020clg400-1，INT8 权重及层输出，截位规则为右移10/9/8后保留8位；42样本的三层共6804项参考输出完全一致。资源为布局布线后的 Vivado report_utilization，全网计算核心采用少量端口包装器，原版外部1024位写入端口固定为不写入，使用已有输入ROM初始化数据，避免将板级输入接口宽度计入比较；两个优化版也采用预加载输入方式。单次计算延迟从接收 start 的时钟沿到 done 有效，不包括外部加载数据和复位时间。原版连续启动间隔用同一输入连续3次启动实测；优化版用48组连续任务实测。吞吐率按1/启动间隔计算，表示内部计算吞吐率，不包含外部传输。

时钟周期是各自本次布局布线满足 setup、hold、脉宽的约束周期，对应频率不是板上测得的频率，也不是对全部布局策略搜索得到的绝对最高频率。本表统一使用单周期时序约束，没有为原版设置多周期路径例外；原版控制器有多拍等待，因此这里的原版周期是保守口径，不能据此断言原版在正确多周期约束下也只能达到这个频率。BRAM按36Kb块统计，半块代表18Kb。所有实现均零布线错误，保存的 DCP 重开复核通过。原版最终周期下42样本功能校验通过，优化版各48组7776项数值/地址校验通过；未上板。

工程与证据：
- 原版课程工程：[Lab6_8.xpr](/home/ding/vivado_project/Lab6/vivado8/Lab6_8.xpr)。此次独立测量保存在 [/home/ding/vivado_project/Lab6_three_version_comparison/original_int8](/home/ding/vivado_project/Lab6_three_version_comparison/original_int8)，原课程工程没有覆盖。
- 资源较省版：[fc2_interleaved_split11](/home/ding/vivado_project/Lab6_architecture_trials/fc2_interleaved_split11)。
- 高并行特色版：[fc1_128x6_dual](/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual)。
- 原版测量脚本：[run_synth.tcl](/home/ding/vivado_project/Lab6_three_version_comparison/original_int8/tools/run_synth.tcl)、[run_impl.tcl](/home/ding/vivado_project/Lab6_three_version_comparison/original_int8/tools/run_impl.tcl)、[run_final_verify.tcl](/home/ding/vivado_project/Lab6_three_version_comparison/original_int8/tools/run_final_verify.tcl)。各版 results 目录保留 utilization_impl.rpt、timing_final.rpt、final_clock.json、final_verify_console.log、route_status.rpt。
- 机器可读数据：[comparison.json](/home/ding/vivado_project/Lab6_three_version_comparison/comparison.json)。
