# Lab5 截位优化试验记录

日期：2026-10-05。原推荐版本保存在原目录。本轮使用独立目录，保留每个候选的 RTL、配置、整数参考、仿真、综合、布线及失败记录。

## 1. 基线和比较口径

基线：`stream_pair256_burst_exact23_tree7_clk4p8`。三层网络 512→128→32→2，168 拍延迟、129 拍启动间隔，原最终布线通过周期 5.26 ns。单次计算 883.68 ns，启动间隔 678.54 ns。资源 23,944 LUT、41,984 FF、61 BRAM Tile、216 DSP。

基线和所有功能候选均检查同样的 48 次连续重叠请求：课程的 42 个样本，加原 Lab5 的课程输入、全 −128、全 127、正负交替、固定种子随机、FC1 极值输入。每个版本逐项检查三层 7,776 个值和地址，验证重叠请求的独立性。分类统计仅使用课程 42 个带标签样本。

使用已有 Lab6 和配套 int8_results.txt 的标签规则：score0 < score1 时预测标签 1，否则为 0，相等归 0。PPT 第 6 页的标签方向与配套数据文件相反；此处保持数据文件和已有工程的规则。未截位基线 37/42（88.10%），错误样本索引为 21、23、25、40、41，索引从 0 开始。

## 2. 课件依据和截位方法

依据 Lab6 第 8～11 页：先完成乘加、偏置和激活，再做层输出截位。42 个原始样本的 FC1/FC2/FC3 最大绝对值为 80,805 / 39,386,422 / 17,379,948,761，与课件一致。后续层的移位根据前层已截位的实际范围重新计算。第 17 页要求三层全截位，并至少比较有符号 4 位和 8 位。

必选 8 位方案使用右移 10 / 9 / 8 位；必选 4 位方案使用 14 / 8 / 9 位，与已有 Lab6 完整整数模型一致。FC2 的 9 位移位基于实际截位后输出范围，未照搬课件举例的 8 位。权重及偏置仍为原模型有符号 INT8，偏置的缩放约定沿用 Lab6。

层间位宽同步缩窄 FC2/FC3 输入、乘积、完整累加器、快照和输出选择总线。FC1 保留 23 位完整累加。FC2 累加宽度为 FC1 输出位宽+15，FC3 为 FC2 输出位宽+13，均覆盖全部对应输入乘加范围。所有层输出量化一次。

floor_wrap：算术右移后选取指定低位，与课件的位选择一致。floor_sat：向下取整并饱和。round_sat：加半个量化步长后算术右移并饱和，恰好半步时向正无穷取整。舍入饱和逻辑均为固定参数，未使用运行时桶形移位器。

额外策略为 FC1 每个 16 位乘积先舍入并丢弃 K 个低位，再送入较窄的加法树，最后恢复 2^K 倍尺度。此策略会改变层数值，是独立的近似试验，不属于原 Lab6 的纯层输出截位。单个乘积误差≤2^(K−1)，512 项 FC1 的最坏绝对误差界为 512×2^(K−1)，该界不保证分类不变。

其中 prereg 方案把乘积舍入放入原乘积输出寄存器之前，减少加法树输入端组合逻辑与寄存器有效位。流水线级数及 168 拍延迟不变。

另有 tree8 方案将 FC1 的两级组合加法拆开，让 8 级加法各自寄存。该版本保留完整乘积，只做 Lab6 的层输出截位，数值与标准 8 位方案相同；延迟由 168 增加为 169 拍，启动间隔仍为 129 拍。最终按照周期数乘通过周期比较单次时间。

K=1～8 的加法树与 FC1 累加位宽还按固定权重、每个输入可取全部 INT8 范围做区间证明：各级节点不溢出，FC1 所有累加前缀均在 23 位范围内。证明见 results/product_width_proof.json。

## 3. DSP 分配和精确打包

standard 保留 FC2 的独立乘法。packed 利用后两层每对输出共享输入，将两个有符号权重组成 (w1<<16)+w0，一次乘法生成两个积，并对高半部做符号修正。该打包运算精确，不增加量化误差。4/6/8 位输入分别穷举 1,048,576 / 4,194,304 / 16,777,216 组 (x,w0,w1)，低积与修正高积均通过。证明记录见 results/packing_proof.txt。

DSP_LANES 指 FC1 中使用 DSP 的打包通道数，其余通道保留原分段逻辑乘法。packed 版本将 FC1 提高到 200 个 DSP，FC2 用 16 个，FC3 用 4 个，总计 220。4 位 LUT 版本将后两层乘法放在逻辑中，FC1 使用 220 个 DSP。DSP 实际总量取自综合/布线报告，不按位宽猜测。

rompack 进一步把固定权重打包提前到初始化数据生成，使 FC2/FC3 权重 RAM 直接输出有符号 25 位打包权重，消除 RAM 与乘法器之间的打包加法。原始权重不变，打包后的数据在各候选 data/fc*_packed_weights.mem 中。该优化在功能上与对应 packed 方案相同。

## 4. 功能和综合候选对比

整数层输出截位搜索共 4,226 组，另检查 FC1 乘积截掉 1～8 位。已生成 20 个 RTL 候选，完成 20 个候选的完整功能检查、15 个综合、9 个完整布线。

| 候选 | 层位宽 | 右移 | 策略 / FC1 低位 | 正确 /42 | 相等数 | 与基线分类不同 | 功能 | 综合 | 布线 |
|---|---|---|---|---:|---:|---:|---|---|---|
| [q8_lab6_d168](/home/ding/vivado_project/Lab5_truncation_optimization/q8_lab6_d168/config.json) | 8/8/8 | 10/9/8 | floor_wrap | 37 | 0 | 0 | passed | passed | passed |
| [q4_lab6_d168](/home/ding/vivado_project/Lab5_truncation_optimization/q4_lab6_d168/config.json) | 4/4/4 | 14/8/9 | floor_wrap | 36 | 27 | 1 | passed | passed | not_run |
| [q8_lab6_d180](/home/ding/vivado_project/Lab5_truncation_optimization/q8_lab6_d180/config.json) | 8/8/8 | 10/9/8 | floor_wrap | 37 | 0 | 0 | passed | passed | not_run |
| [q8_lab6_pack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_lab6_pack_d200/config.json) | 8/8/8 | 10/9/8 | floor_wrap | 37 | 0 | 0 | passed | passed | passed |
| [q4_lab6_lut_d220](/home/ding/vivado_project/Lab5_truncation_optimization/q4_lab6_lut_d220/config.json) | 4/4/4 | 14/8/9 | floor_wrap | 36 | 27 | 1 | passed | passed | passed |
| [q6_6_6_round_pack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q6_6_6_round_pack_d200/config.json) | 6/6/6 | 12/10/7 | round_sat | 38 | 0 | 1 | passed | passed | passed |
| [q8_8_8_round_pack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_8_8_round_pack_d200/config.json) | 8/8/8 | 12/7/8 | round_sat | 38 | 0 | 1 | passed | passed | not_run |
| [q8_6_8_round_pack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_6_8_round_pack_d200/config.json) | 8/6/8 | 12/10/5 | round_sat | 38 | 0 | 1 | passed | passed | not_run |
| [q4_8_8_round_pack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q4_8_8_round_pack_d200/config.json) | 4/8/8 | 13/6/8 | round_sat | 38 | 0 | 1 | passed | passed | not_run |
| [q8_product1_pack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_product1_pack_d200/config.json) | 8/8/8 | 10/9/8 | floor_wrap / K=1 tree | 37 | 0 | 0 | passed | not_run | not_run |
| [q8_product2_pack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_product2_pack_d200/config.json) | 8/8/8 | 10/9/8 | floor_wrap / K=2 tree | 37 | 0 | 0 | passed | not_run | not_run |
| [q8_product3_pack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_product3_pack_d200/config.json) | 8/8/8 | 10/9/8 | floor_wrap / K=3 tree | 37 | 0 | 0 | passed | not_run | not_run |
| [q8_product4_pack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_product4_pack_d200/config.json) | 8/8/8 | 10/9/8 | floor_wrap / K=4 tree | 37 | 0 | 0 | passed | passed | passed |
| [q8_product6_pack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_product6_pack_d200/config.json) | 8/8/8 | 10/9/8 | floor_wrap / K=6 tree | 37 | 0 | 0 | passed | not_run | not_run |
| [q8_product8_pack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_product8_pack_d200/config.json) | 8/8/8 | 10/9/8 | floor_wrap / K=8 tree | 38 | 0 | 1 | passed | not_run | not_run |
| [q8_product4_prereg_pack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_product4_prereg_pack_d200/config.json) | 8/8/8 | 10/9/8 | floor_wrap / K=4 register | 37 | 0 | 0 | passed | passed | not_run |
| [q8_product6_prereg_pack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_product6_prereg_pack_d200/config.json) | 8/8/8 | 10/9/8 | floor_wrap / K=6 register | 37 | 0 | 0 | passed | passed | passed |
| [q8_lab6_rompack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_lab6_rompack_d200/config.json) | 8/8/8 | 10/9/8 | floor_wrap | 37 | 0 | 0 | passed | passed | passed |
| [q8_product6_prereg_rompack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_product6_prereg_rompack_d200/config.json) | 8/8/8 | 10/9/8 | floor_wrap / K=6 register | 37 | 0 | 0 | passed | passed | passed |
| [q8_lab6_tree8_rompack_d200](/home/ding/vivado_project/Lab5_truncation_optimization/q8_lab6_tree8_rompack_d200/config.json) | 8/8/8 | 10/9/8 | floor_wrap / tree8 | 37 | 0 | 0 | passed | passed | passed |

not_run 表示该阶段未运行，不代表时序通过或失败。仅进行功能检查的低位数方案保留作误差对照，硬件优先实现能明显缩窄加法树的候选。未布线方案不参与速度排名。

## 5. 完成布线的性能比较

| 方案 | 拍数 | 通过周期 ns | 时延 ns | 启动间隔 ns | LUT | FF | BRAM | DSP | WNS ns | WHS ns | WPWS ns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 原 Lab5 最佳 | 168 | 5.26 | 883.68 | 678.54 | 23944 | 41984 | 61 | 216 | 0.005 | 0.050 | 1.650 |
| q8_lab6_tree8_rompack_d200 | 169 | 5.04 | 851.76 | 650.16 | 20075 | 40600 | 61 | 220 | 0.007 | 0.050 | 1.156 |
| q8_lab6_rompack_d200 | 168 | 5.08 | 853.44 | 655.32 | 20059 | 36442 | 61 | 220 | 0.008 | 0.008 | 1.196 |
| q8_lab6_d168 | 168 | 5.18 | 870.24 | 668.22 | 23003 | 40211 | 61 | 200 | 0.006 | 0.011 | 1.610 |
| q8_product6_prereg_rompack_d200 | 168 | 5.22 | 876.96 | 673.38 | 15610 | 35700 | 61 | 220 | 0.002 | 0.050 | 1.336 |
| q4_lab6_lut_d220 | 168 | 5.30 | 890.40 | 683.70 | 19304 | 34533 | 61 | 220 | 0.004 | 0.007 | 1.670 |
| q8_lab6_pack_d200 | 168 | 5.33 | 895.44 | 687.57 | 20229 | 36366 | 61 | 220 | 0.002 | 0.050 | 1.685 |
| q8_product4_pack_d200 | 168 | 6.67 | 1120.56 | 860.43 | 18618 | 30219 | 61 | 220 | 0.001 | 0.014 | 2.355 |
| q8_product6_prereg_pack_d200 | 168 | 6.68 | 1122.24 | 861.72 | 15779 | 32787 | 61 | 220 | 0.009 | 0.008 | 2.360 |
| q6_6_6_round_pack_d200 | 168 | 6.94 | 1165.92 | 895.26 | 20270 | 32358 | 61 | 220 | 0.003 | 0.015 | 2.490 |

综合和布线器件均为 xc7z020clg400-1。统一初始目标 4.8 ns，使用 Explore 布局、物理优化及布线。每个完成布线的设计按 0.01 ns 分辨率重新约束，保存通过周期的 timing_final.rpt、final_routed.dcp、final_clock.xdc，同时保留再缩短 0.01 ns 的 timing_boundary.rpt。只将 setup、hold、pulse width 均通过的结果列入此表；4.8 ns 的负 WNS 不算达到该频率。

## 6. 当前选择与精度结论

保持这 42 个样本分类与基线一致的最快完成方案：**q8_lab6_tree8_rompack_d200**。通过周期 5.04 ns，延迟 851.76 ns，比原最佳减少 3.61%，速度比 1.038。准确率 37/42，相等数 0。

相对原基线，LUT 变化 -16.16%，FF 变化 -3.30%，BRAM 61，DSP 220。

只做层输出截位、保持已有 Lab6 8 位整数结果的完成方案：**q8_lab6_tree8_rompack_d200**，周期 5.04 ns，延迟 851.76 ns。若需要严格遵循课件“完整 MAC 后截位”的口径，可选择该版本。

在本轮完成且不慢于原基线的方案中，较省 LUT 的版本是 **q8_product6_prereg_rompack_d200**：15610 LUT、35700 FF，周期 5.22 ns、延迟 876.96 ns。该版本包含乘积近似时应按配置中的 product_cut 判断，与 Lab6 标准层输出截位数值不同。

较均衡的纯层截位版本是 **q8_lab6_rompack_d200**：853.44 ns，36442 FF。最快 tree8 版本仅比它减少 0.197% 单次时间，却多用 4158 FF。若更重视寄存器资源，可采用该 7 级版本。

4 位原方案 36/42（85.71%），但 27 个样本分数相等，其中多数按默认标签 0 得分，因此分类信息损失明显。8 位原方案 37/42（88.10%），没有相等分数，分类与基线一致。部分舍入方案达到 38/42（90.48%）。这些移位和位宽由同一组 42 样本选择，38/42 属于这组数据的观察结果，尚不能据此判断未见数据准确率提高。

floor_wrap 的移位按课程输入范围校准，在课程 42 样本上无溢出，但极值输入会回绕。各 config.json 的 overflow_counts 记录 42 样本越界数，stress_overflow_counts 记录全部 48 请求。饱和版本避免回绕，但可能剪掉幅值。

不采用为最快方案的原因：单纯增加 DSP 并做动态权重打包，完成周期为 5.33 ns；加法树入口舍入版本为 6.67 ns，其关键路径转移到 FC2 权重 RAM、打包加法与 DSP 之间；寄存器前舍入但仍动态打包为 6.68 ns。提前打包到 ROM 后，这类路径改善到 5.22 ns，且只用 15,610 LUT，但仍慢于不做乘积近似的 5.08 ns。标准 4 位和 6 位舍入版本的通过周期分别为 5.30 / 6.94 ns，均未提供更快单次时间。

## 7. 复现与文件

输入与模型沿用原最佳版本的初始化 ROM。42 样本和六组扩展输入通过测试平台更换 ROM 内容进行功能验证；现有物理接口没有运行时加载输入端口。本轮物理资源和时序均使用与基线相同的课程样本 1 ROM 初始化。换物理 ROM 输入时需更新初始化文件并重新综合，资源和时序也可能随初始化数据改变。

构建脚本：tools/search_quantization.py、tools/build_candidates.py。搜索结果：results/quantization_search.csv / .json。逐候选数据：config.json、data/fc*_expected.mem、results/rtl_samples.csv。资源及时序对比：results/hardware_comparison.csv / .json。各阶段完整日志、耗时和状态：results/*_console.log、results/run_status.json。

运行指定候选：

```sh
cd /home/ding/vivado_project/Lab5_truncation_optimization
python tools/run_trials.py sim <候选名>
python tools/run_trials.py synth <候选名>
python tools/run_trials.py impl <候选名>
python tools/collect_results.py
python tools/write_report.py
```

Vivado 仿真/布线使用 general.maxThreads=8，后续综合使用 4，以控制综合子进程的内存占用；首两份综合日志实际使用 8。各阶段耗时是本机实际运行记录，部分阶段同时运行，且存在热状态与内存负载差异，不用这些耗时断言某线程设置必然更快。

时序结论适用于已约束内部时钟路径，外部 IO 延迟和板级引脚尚未定义，未做板上实测。保存的 DCP 是完成布线的设计，单次时间由已验证拍数与通过周期相乘。

## 8. 最终工程和复核

推荐版本的保存 DCP 已重新打开，复核 setup、hold、pulse width 通过，布线错误数为 0。导出工程按 5.04 ns 设置时钟，并在这个参数下重新完成 48 次重叠请求、7,776 个值和地址检查，errors=0。记录见 results/final_verification_console.log、候选 results/timing_verified.rpt 和 results/route_status_verified.rpt。

[可直接打开的 Vivado 推荐工程](/home/ding/vivado_project/Lab5_truncation_optimization/recommended/Lab5_truncation_recommended.xpr)

[推荐版本完成布线的 DCP](/home/ding/vivado_project/Lab5_truncation_optimization/q8_lab6_tree8_rompack_d200/results/final_routed.dcp)

本轮 20 个 RTL 候选的功能检查、15 个候选综合和 9 个候选完整布线已全部按计划完成。最佳结果指本轮已完成的这些实施结果，不代表全局最优。
