# Lab 项目 Codex 交接

> 2026-10-08 本地精简更新：7 组已确认失败试验的完整工程目录已删除，文字、源码、输入数据、日志与报告归档位于 `/home/ding/vivado_project/失败试验记录/2026-10-08/`，并同步 GitHub 的 `failed_experiments/2026-10-08/`。具体目录见 `cleanup_receipt.json`；这些归档不包含 DCP 和大型波形，历史条目中的原失败工程路径可能已失效。代表工程、共享数据、暂停未完成及仅性能较差的版本保留。

更新日期：2026-10-06。用途：在本机 Codex 中继续已有工程，无需用户重新复述。根据已读取的聊天历史整理，并再次核对推荐结果 JSON、倍频仿真及布线报告。历史聊天结论不等于当前工程状态；遇到冲突，以对应最终文件和验证记录为准。

## 用户明确的停止条件

用户于2026-10-06明确要求：**没有明显改善预期的情况下就停下。** 后续任何优化试验应先依据当前瓶颈、资源预算和已有结果，说明预期改善及其依据；若缺乏可信的明显收益预期，应停止优化，不自动追加相似候选或反复微调。不能仅因还有方案可试而继续耗费时间。历史约1%的改善门槛可作为参考，但不能把刚超过门槛当作自动继续的理由。

## 最新追加：架构优化试验（2026-10-06）

**当前最新已验证最快整网为 `fc2_interleaved_split11`：174拍×4.09 ns=711.66 ns，比735.30 ns缩短3.215%。** 启动间隔129拍=527.61 ns。LUT15782、FF37767、BRAM68、DSP220；WNS +0.001、WHS +0.007、WPWS +0.206 ns，TNS/THS/TPWS=0、布线错误0。最终时钟下48个重叠请求、7776项输出/地址检查零错误，37/42正确、无平局；保存DCP重开验证通过。尚未门级仿真或上板。

工程根目录 `/home/ding/vivado_project/Lab6_architecture_trials`；选中版本 `results/selected.json`，完整比较 `results/comparison.json`。候选目录 `fc2_interleaved_split11` 内 `results/final_routed.dcp` 与 `results/final_clock.xdc` 是最终结果，`tools/run_final_verify.tcl` 为最终复核脚本。Vivado工程在 `vivado/fc2_interleaved_split11.xpr`，但原始timing.xdc仍4.4 ns实现目标，须使用最终时钟约束才能复现4.09 ns检查。

改动为FC2偶/奇交错部分和、11+10位分段反馈及分段末尾合并，增加3拍但降低周期。新关键路径位于FC1加法树。旧recommended/与735.30 ns候选保持原样，下文历史“当前最佳”以本段为准。

本轮两种FC1 SIMD/PE组织已完成布线：128×4为889.14 ns，64×8为847.83 ns，均慢于基线，未采用。还试INT4四乘法打包单元和离线剪枝/低位量化。完整结果与失败原因见 `/home/ding/桌面/Lab/Lab6架构优化试验记录.md`。INT4单元综合1 DSP/69 LUT/90 FF且穷举正确，但未整网实现；全网直接INT4损失显著。剪枝仅42样本离线验证，未重训练、未见数据评估、无硬件测量，不能声称等价或泛化改善。

## 交接后追加：本轮快速试验最新结果

用户随后要求继续快速尝试。本轮从原 741.20 ns 基线独立复制两个 FC2 候选，没有覆盖旧推荐 RTL。

**最新已验证最快候选：`quick_fc2_rom_pipe`，171 拍 × 4.30 ns = 735.30 ns，比 741.20 ns 快 0.796%。** 启动间隔 129 拍 × 4.30 ns = 554.70 ns。LUT 15734、FF 35596、BRAM 68、DSP 220；WNS +0.001 ns、WHS +0.013 ns、TNS/THS/TPWS 为 0、WPWS +0.416 ns、布线错误 0。最终 4.30 ns 下 48 个重叠请求、7776 项检查均通过，保存的 DCP 重新打开验证 setup/hold 通过。仍非门级仿真或上板验证。

改动是在 FC2 权重和数据输入链各加一级流水，同时匹配 valid/first/last 延迟。综合把新增权重流水吸收进 DSP，FC2 BRAM 仍 DOA_REG=0；不能声称已经启用 BRAM 输出寄存器。最终关键路径变为 FC2 product_r→acc，延迟 4.275 ns。观察到的收益属于本次整体实现结果，不能把全部收益都归因于单一结构变化。

新候选目录 `/home/ding/vivado_project/Lab6_limit_search/quick_fc2_rom_pipe`；最终检查点 `results/final_routed.dcp`，最终仿真 `results/final_verify_console.log`，选中记录 `/home/ding/vivado_project/Lab6_limit_search/results/quick_fc2_selected.json`。两个试验汇总见 `results/quick_fc2_results.json`。旧 `recommended/` 和 `recommended.json` 保留为 741.20 ns 稳定基线，尚未覆盖。

第二个 `quick_fc2_keep_weight` 候选最终需 4.88 ns，170 拍为 829.60 ns，比原基线慢 11.927%，未采用。详细结果见 `/home/ding/桌面/Lab/Lab6快速FC2优化结果.md`。

收益小于约定的 1% 明显改善门槛，本轮只完成这两个候选后停止，不自动添加新一轮。下文“推荐版”和 741.20 ns 指交接时保存的基线，当前工作继续时应先查看本追加结果。

## 先读这些结论

- 当前全网络最佳已验证版本是 Lab6 `prepack_banked_lookup`，推荐入口 `/home/ding/vivado_project/Lab6_limit_search/recommended/Lab6_limit_recommended.xpr`。
- 全网络延迟 **170 拍 × 4.36 ns = 741.20 ns**；启动间隔 **129 拍 = 562.44 ns**。延迟和吞吐间隔不可混用。
- 最近 DSP 两倍频小原型数值仿真通过，但约 459 MHz 的布线时序失败。它不是新的推荐版本，也没有完成全网络集成或上板验证。
- 本轮交接只整理记录，没有重新综合、布线或修改推荐 RTL。
- 保留本机工程目录即可继续。不要只复制桌面课程目录或一个 `.xpr` 文件；实际 RTL、数据及脚本在 `/home/ding/vivado_project`，且有跨目录和绝对路径依赖。

## 环境与入口

| 项目 | 位置或说明 |
|---|---|
| 课程资料、PPT、PDF、参考输出 | `/home/ding/桌面/Lab`，包含 Lab1 至 Lab6 |
| 实际 Vivado 工程与历史试验 | `/home/ding/vivado_project` |
| Vivado | `/vivado/2025.2/Vivado/bin/`，版本 2025.2 |
| FPGA | `xc7z020clg400-1`，Zynq-7020，DSP48E1，220 个 DSP |
| 网络 | 512 → 128 → 32 → 2，原始 int8 权重与偏置 |
| 本轮机器观察 | 16 个逻辑 CPU，约 22 GiB RAM；空闲内存会变化 |
| 调研文件 | `/home/ding/桌面/Lab/Lab5截位优化资料调研.md` |

当前聊天为 **Lab6优化接力**，ID `01a10d44-a4b7-7053-8ecc-bd62cc9e5d95`，工作目录 `/home/ding/桌面/Lab`。已有历史可以继续使用。建议保持本机执行，沿用现有 Vivado、许可和路径。

## 原推荐工程：保留的比较基线

| 指标 | 最终记录 |
|---|---:|
| 延迟 | 170 拍，741.20 ns |
| 启动间隔 | 129 拍，562.44 ns |
| LUT / FF | 15755 / 35454 |
| BRAM / DSP | 68 / 220 |
| WNS / WHS | +0.003 ns / +0.012 ns |
| TNS / THS | 0 / 0 |
| WPWS / TPWS | +0.476 ns / 0 |
| 布线错误 | 0 |

关键文件：

- 机器可读结果：`/home/ding/vivado_project/Lab6_limit_search/results/recommended.json`。
- 推荐工程：`/home/ding/vivado_project/Lab6_limit_search/recommended/Lab6_limit_recommended.xpr`。
- 推荐 RTL、数据、TB、约束：该目录下 `rtl/`、`data/`、`tb/tb_quant.v`、`timing.xdc`。
- 选中实现与报告：`/home/ding/vivado_project/Lab6_limit_search/prepack_banked_lookup/results/`。
- 已布线检查点：上述目录 `final_routed.dcp`。

注意 JSON 中 `source` 字段仍指向 `prepack_banked_rom`；选中版本应结合 `name=prepack_banked_lookup`、`rtl_source`、`checkpoint` 和推荐导出工程判断，不能只看一个旧字段。

验证范围：48 个重叠请求（42 个课程样本及 6 个扩展请求），7776 个分层输出/地址检查，数值错误 0。课程分类正确 37/42、平局 0；分类准确率与硬件参考数值一致性是两件事。最终时钟下导出的选中 RTL 仿真通过；不是门级仿真，也没有据此确认板上运行。

结构：FC1 使用 200 个 DSP，FC2 使用 16 个，FC3 使用 4 个。FC1 为 256 个成对计算通道，每个输入完成两项乘积，分两组输入；其中 56 个通道由 LUT 补充。层间流式传递，不能按早期串行工程的整层输入 RAM 结构理解。

最终关键路径在 FC2 权重 RAM 到 DSP A 输入：3.947 ns，其中逻辑 2.454 ns、布线 1.493 ns。不能继续默认 FC1 是当前最差路径。

## 数值规则：后续优化必须保持

- 层输出均为 8 位，右移量依次 10、9、8；`ROUND=0`、`SAT=0`。
- 使用有符号算术右移，再取低 8 位，溢出回绕。不要替换成饱和、四舍五入或逻辑右移。
- ReLU 位于缩窄之前，因此缩窄后仍可能回绕为负值，下一层不能擅自按无符号 8 位解释。
- 分类规则：`score0 < score1` 判为 1，否则判为 0。课程 PPT 的标签方向与现有 `int8_results.txt` 有差异，沿用已验证参考，不自行翻转。
- 当前固定权重范围证明：FC1 `[-3575930,3574270]` 可用 23 位；FC2 全部前缀 `[-874237,875063]` 可用 21 位；FC3 `[-251408,252217]` 可用 19 位。更换权重、累加顺序或量化规则时，重新证明，不能照搬。

## 最近倍频试验：保存为失败的可复现记录

根目录：`/home/ding/vivado_project/Lab6_dsp_multipump_probe`。目的：用 16 个 DSP 在两个快时钟时隙完成原本 32 个 DSP 的成对乘法，先验证小块可行性。

| 版本 | 数值验证 | 实现结果 |
|---|---|---|
| 初版 `rtl/mp_probe.v` | 2048 帧、131072 项独立乘积，错误 0 | LUT 398、FF 4055、BRAM 8、DSP 16；内部 WNS -1.571 ns，失败 |
| 修正版 `registered/` | 同规模最终错误 0 | LUT 403、FF 4524、BRAM 8、DSP 16、BUFG 3、MMCM 1；时序失败 |
| 对照 `baseline_results/` | 用于资源比较 | 32 DSP、LUT 32、FF 1024、BRAM 8；外部虚拟接口存在保持时间问题，不是已通过时序的板级对照 |

修正版使用显式 DSP48E1 流水寄存器、BRAM 后补级，以及 MMCM/BUFG 时钟包装；主时钟 4.36 ns，快时钟 2.18 ns，约 458.7 MHz。

最终证据文件：

- `registered/results/simulation.log` 和 `registered/sim/xsim.log`：`frames=2048 individual_products=131072 errors=0`。
- `registered/results/timing.rpt`：WNS **-1.825 ns**、TNS -3088.732 ns；WHS **-3.343 ns**、THS -1140.751 ns，明确未满足约束。
- `registered/results/internal_paths.rpt`：快时钟内部 WNS **-1.796 ns**，`core/phase_reg` 至 DSP 输入的路径 3.592 ns，约 80% 为布线延迟，时隙选择信号扇出是明显问题。
- `registered/results/utilization_impl.rpt`、`clock_interaction.rpt`、`drc.rpt`、`routed.dcp` 保存资源、跨时钟、DRC 和布线状态。

验证边界：仿真验证了理想相关时钟下的小核心计算和慢域结果重组，没有验证 MMCM 启动后的相位对齐，没有全网络集成，没有完整真实板级引脚/接口约束。虚拟大量数据 IO 仍有 DRC 问题；有 routed.dcp 不代表可以上板。

历史日志包含一次仿真启动期 15 项错误：DSP 模型 `glbl` 的 100 ns GSR 启动期导致，最终 TB 已等待 150 ns 后解除复位，重新仿真为 0 错误。不要拿 backup.log 当最终结果；也不要删掉它掩盖过程。

`create_probe.py`、`fix_probe.py` 是生成阶段脚本，最终 RTL/TB 后续做过修补；直接重跑可能覆盖最终修改，先比较当前文件。试验没有提高当前全网络性能。

理论预算仅供筛选：若 FC1 全部按两时隙复用，可能用 128+16+4=148 DSP，比 220 少 72 个；尚未实现，额外寄存器和选择布线不可忽略。6400 位/主拍的权重带宽不会自动减少，BRAM 也不会自动减半。在 200 MHz 下 170 拍为 850 ns；至少降至 148 拍才超过 741.20 ns，146 拍才超过约 1% 收益。

## Lab 相关聊天逐项交接

以下为检索到的 12 个原 Lab 项目聊天、1 个归档聊天，并补充本次迁移讨论。标题按当前列表记录；本节是摘要，不是逐字聊天导出。

### 1. 梳理各 Lab 任务与上板节点

ID：`01a0cc8c-1426-7ba0-b9d8-3704e1369bab`。

- 主题/完成：通读课程资料，区分无板可做的代码、仿真与必须上板的步骤；随后处理 Lab1 IP 封装、时钟和 AXIS 接口关联、Zynq PS 与 DMA 配置。
- 文件：课程 `/home/ding/桌面/Lab/Lab1/资料/实验一指导书.pdf`；工程 `/home/ding/vivado_project/Lab1`、`Lab1_re`。
- 结论：时钟设置关注 `FREQ_HZ=100000000`；课程 DMA 配置为 SG 关闭、地址 32 位、MM2S 内存/流 64/64 位、S2MM 32/64 位，两向 burst 256、各一通道。
- 待办：未获得完整板上验证证据；最近记录到 PS 初始化后添加 DMA，不能宣称整个 Lab1 已上板完成。

### 2. 文档里的axi direct memory access没有m_axi_sg_aclk端口，而我这里有，并且不连接它会…

ID：`01a0cd98-5dff-70a2-874f-30fa35786c26`。标题为界面显示的截断标题。

- 主题/完成：解释 DMA 的 SG 时钟与地址段报错；简单 DMA 可关闭 SG，若保留 SG 则需补齐互连、时钟、复位和地址。随后解释 Lab2 移位、计数器、多路选择器、RTL 与波形。
- 文件：`/home/ding/vivado_project/Lab2_4_to_1`、`Lab2_8_3_encoder`；课程 `/home/ding/桌面/Lab/Lab2.pptx`。
- 结论：修正类似 `2d'00` 的 Verilog 常量写法为 `2'd0`，关注组合逻辑默认分支。
- 待办：这些教学解释不构成 DMA 整套系统上板成功的证据；之后如做板级集成需检查实际 block design。

### 3. 解释 rd_addr 与 rd_addr_ptr 逻辑

ID：`01a0ce17-5eab-7470-8046-7627c204db54`。

- 主题/完成：解释同步 FIFO 指针多一位区分回绕，低位用作 RAM 地址；异步 FIFO Gray 指针与两级同步、空满判断延迟。
- 文件：`/home/ding/桌面/Lab/Lab3` 课程资料；相关工程 `Lab3_sync_fifo`、`aync_fifo`。
- 结论：PPT 第 7 页类似 `[addr_width-1:addr_width]` 的反向切片疑似笔误，正确地址通常为 `[addr_width-1:0]`；必须结合实际代码检查。
- 待办：概念解释不是完整 CDC 或亚稳态可靠性验证。

### 4. 提取同步 FIFO 测试台

ID：`01a0d115-3a3f-74a3-8351-d5d3c51afe70`。

- 主题/完成：提取 TB，随后检查异步 FIFO 仿真与波形配置。工程名实际拼为 `aync_fifo`，不要随意更名导致路径失效。
- 文件：`/home/ding/vivado_project/Lab3_sync_fifo`、`/home/ding/vivado_project/aync_fifo/aync_fifo_tb_behav.wcfg`。
- 结论：约 5 μs 仿真中写读指针 0→10，10 次 valid，读值均为 FFFF，empty 恢复、full 为 0。文件只有 9 行是 TB 提前关闭文件再写第十项的问题，不能判为 FIFO 少读一项。
- 待办：修复 TB 文件关闭位置；改用不同数据检查顺序和边界，全 FFFF 不足以证明顺序正确。

### 5. 完成 Lab4

ID：`01a0d6a1-6b76-7951-bad7-c410d3241fec`。

- 主题/完成：补全 `fc.v`、乘法阵列、加法树、顶层与 BRAM IP 连接，建立参考输出检查；解释组/通道索引、权重地址、数据延迟匹配。
- 文件：`/home/ding/vivado_project/Lab4`；说明文档 `/home/ding/vivado_project/Lab4/output/docx/Lab4代码与仿真操作说明.docx`。
- 结论：IP 端口应按实际生成 wrapper 连接，包括 ena/rsta 等，不能照搬别版本示例。
- 待办：该早期文档不代表后续最终验证状态。完整 128 输出通过记录应看下一项 Lab4 优化结果。

### 6. 解释全连接层计算方式

ID：`01a0dd9b-470b-7a52-9b3c-1f4c6678d106`。

- 主题/完成：解释乘加计算、512 输入到 128 输出、128 并行通道分 4 组的组织方式，以及权重地址 `4*channel+group` 与数据有效标志延迟。
- 文件：沿用课程 Lab4 和 `/home/ding/vivado_project/Lab4`，没有独立的新优化成果。
- 待办：实际改变流水级后必须重新匹配 BRAM、乘法、加法树和有效信号，不能只改数值位宽。

### 7. 评估Lab4并开始Lab5

ID：`01a0ed60-c60c-7c33-b082-4d3ce20d2ed2`。

- 主题/完成：建立符合课程要求的基本 Lab5，FC1、FC2、FC3 分开实现；FC1 输出 32 位带 ReLU、FC2 48 位带 ReLU、FC3 64 位无激活。
- 文件：`/home/ding/vivado_project/Lab5/vivado/Lab5.xpr`、该工程 README 和 data/reference；课程参考 `/home/ding/桌面/Lab/Lab5/输出特征图参考/FCNet/features/`。
- 结论：课程 128/32/2 层输出匹配，最终两值 1444462170、-1667237270。早期共享参数化模块/提前截位方向曾被用户纠正，课程原版与后续优化版应分别保存。
- 待办：仿真需 run all 或足够时间（至少约 20 μs），默认 1000 ns 不足。此前多个 IP 生成任务并发耗尽内存，不要把“调用全电脑”理解为无限并发。

### 8. 概括截位的原因和方法

ID：`01a0f118-e812-7791-b69b-0bffb931ae65`。

- 主题/完成：阅读 Lab6 PPT，解释量化/截位；建立串行 8 位与 4 位参考实现、数据、TB、脚本。
- 文件：`/home/ding/vivado_project/Lab6/rtl/lab6_top.v`、`lab5_controller.v`、`cut_fc_layer.v`；`Lab6/vivado8/Lab6_8.xpr`、`Lab6/vivado4/Lab6_4.xpr`。
- 结论：该聊天解释的“层输出 BRAM 再搬到下层输入 RAM”适用于早期串行实现，不适用于当前流式最佳版本。课程样本幅值观察不是所有输入的严格范围证明。
- 待办：保留为量化与功能参考；后续量化规则以当前最佳版本的验证为准。

### 9. Lab4优化

ID：`01a1058d-64a8-7df2-b037-8f9c72b412bd`。

- 主题/完成：比较并行度、权重打包、累加器和加法树流水布局，多次独立实现；最终 4.3 ns 通过，4.2 ns 未通过后停止。
- 文件：代表最终工程 `/home/ding/vivado_project/Lab4_tree4_1221_full4p3/Lab4.xpr`；报告 `/home/ding/vivado_project/Lab4_optimized/adder_experiments/Lab4资源演进与代表版本.md`、`后续时序优化报告.md`、`加法结构对比报告.md`，以及 `Lab4_optimized/并行度对比报告.md`、`优化操作报告.md`。
- 结论：最终 LUT 1189、FF 2005、DSP 64、BRAM 22.5，WNS +0.025 ns、WHS +0.107 ns，128 输出通过。属于计算核心验证，未包含真实板级 IO 约束。
- 历史：原 128 路版本 LUT 4587、FF 7061、DSP 128、BRAM 29.5；更少资源不一定最低延迟。地址扇出曾是瓶颈，之后瓶颈变化，不能永久按旧结论优化。
- 待办：继续 Lab4 时优先读取最终报告，避免重新跑已失败布局。

### 10. 回顾 Lab5 内容

ID：`01a1073e-c2d2-7773-9288-65528b239114`。

- 主题/完成：发展流式层间传递，FC1→FC2、FC2 每四输出→FC3，消除不必要的层间输入 RAM；做固定权重精确位宽与通用位宽比较。
- 文件：`/home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8`；`/home/ding/vivado_project/Lab5_final_optimized` 是指向它的符号链接。
- 结论：未截位 Lab5 代表版本 168 拍×5.26 ns=883.68 ns，启动间隔 129 拍=678.54 ns；LUT 23944、FF 41984、BRAM 61、DSP 216。内部宽度 23/35/45，外部 32/48/64 位符号扩展。
- 注意：目录名 `clk4p8` 是曾经的目标，不能当作通过周期；默认 GUI impl1 在 4.8 ns 下 WNS -0.398，最终保存的 impl_explore 为 5.26 ns。通用 25/40/53 位资源略高，同样 5.26 ns。
- 待办：这是未截位 Lab5 基线，不应覆盖当前 Lab6 741.20 ns 推荐版本。

### 11. Lab6截位优化方案

ID：`01a10b8a-3cb3-7eb3-86d6-2a2a8426ff68`；此前被用户称为“探索Lab5截位优化方案”。

- 主题/完成：从 Lab5 流式版发展截位优化，检查数值范围、FC2 瓶颈、权重 ROM 分银行与预打包、查表交叉乘积；最终产生当前推荐结果。
- 文件：`/home/ding/vivado_project/Lab5_truncation_optimization`、`Lab6_bottleneck_optimization`、`Lab6_limit_search`，后者 `results/recommended.json` 是当前选择入口。
- 结论：以本文件“当前最佳工程”一节为最终结果。512 路 `dual512_lookup` 虽可降至 107 拍，但 CARRY4 需求 14014 超过容量 13300；后来混合树也存在布局失败，不能只看拍数继续扩大。
- 用户约束：先估计资源，不强推 512 路，不以大量 LUT 乘法器硬堆并行度；连续无明显收益应停。最后提出评估 DSP 复用，由本聊天继续。
- 待办：旧聊天被中断不意味着其试验需要重跑。恢复时保留所有失败记录，先确认最终 JSON 与 DCP。

### 12. Lab6优化接力（本聊天）

ID：`01a10d44-a4b7-7053-8ecc-bd62cc9e5d95`。

- 主题/完成：检索类似 FPGA 截位、DSP 打包/倍频、并行调度、存储和时序方法，形成 12 类方法及主要资料链接；评估优先级，完成 16 DSP 两倍频小原型与修正版。
- 文件：`/home/ding/桌面/Lab/Lab5截位优化资料调研.md`、`/home/ding/vivado_project/Lab6_dsp_multipump_probe`、本交接文件。
- 结论：调研属于候选方案；倍频是已试验但未通过时序的方向。推荐仍为 741.20 ns，全网络性能没有因此刷新。
- 待办：按小原型的失败路径决定是否值得继续；不要先集成全网络。用户希望快速结果，下一次工作先给清楚预算与停止条件。

### 13. 搜索 Lab5 截位优化方案（已归档）

ID：`01a10d44-1703-7680-8491-0e61d58a9873`。

- 主题：一次独立搜索入口，随即中断。
- 完成/文件：读取的记录没有独立产物或实施结果。
- 待办：无需恢复或重复搜索；有效调研与试验集中于上一项。

### 14. 评估项目是否需要转用 Codex（本次衔接讨论）

ID：`01a10d65-1d11-7852-9e8e-13dedb6aa025`，工作目录同为 `/home/ding/桌面/Lab`。

- 主题/完成：讨论 Work 与 Codex 的差异，用户明确表示打算尝试 Codex，并接回本项目聊天完成交接。
- 文件：本交接文件；没有新的 RTL、综合或布线成果。
- 待办：在本机沿用现有目录继续即可，不需要另起一个丢失上下文的工程。普通“Codex和GPT Work区别”讨论不作为 Lab 技术成果来源。

## 目录迁移与复现注意

1. 推荐 RTL 还引用 `/home/ding/vivado_project/Lab5_optimization/data/` 下的偏置及输入数据；不能只带走 `recommended/`。
2. 倍频原型使用推荐版本 FC1 bank0/1 权重，以及 `Lab5_optimization/data/stream_pair256_hybrid_inputs.mem`。
3. `Lab6_limit_search/tools/run.py` 导入 `/home/ding/vivado_project/Lab6_bottleneck_optimization/tools` 的 runner，迁机时需同时保存或修改依赖。
4. 很多 `.mem` 和 Tcl 使用绝对路径；先检索依赖再迁机，不能假设 `.xpr` 自动携带数据。
5. `Lab5_final_optimized` 是符号链接，要保存真实目标。优先保存 RTL、数据、TB、Tcl、XDC、范围证明、结果 JSON、报告和 DCP；缓存不应取代这些证据。
6. 当前未发现适用的 AGENTS.md，也未确认这些工程存在可用 Git 仓库；不要假设可直接创建 Git worktree。
7. Vivado 内部 maxThreads=8 与同时启动 8 个大型任务是不同的资源负担。先估内存，多个 IP 生成/实现进程可能耗尽 RAM。

## 后续工作建议与停止条件

默认先保持推荐版作为可交付结果。若继续追求更快，优先检查当前 FC2 RAM→DSP 路径，做小范围的寄存器/数据组织预算；其次再比较输入与输出并行度分配。每个候选先说明预期拍数、频率、DSP/LUT/BRAM/FF 需求，再决定是否实现。

倍频方向只有在小块能降低 phase 选择扇出、解决慢快时钟传递与保持时间，并验证 MMCM 启动相位后，才值得集成。不能用假路径或不合理多周期约束隐藏真实数据传递问题。

比较统一采用完整网络延迟、启动间隔、资源、参考数值一致性及布线后的 setup/hold/脉宽结果。降低拍数但频率变慢、仅综合通过或仅理想时钟仿真通过，都不能宣称优于 741.20 ns。

用户已要求：不盲目强推 512 路、不用巨大 LUT 阵列补 DSP 缺口；明显方向试完或连续改动收益不足约 1% 时停止，保存记录并报告判断。当前结果只能称为已尝试范围内最佳，不能声称全局最优。

## 可直接用于下一次开工的提示

请先阅读本文件、`Lab6_limit_search/results/recommended.json` 和倍频修正版最终报告。沿用本机 Vivado 2025.2 与已有目录，以 741.20 ns 推荐工程为基线，保持已验证截位和分类规则。先评估当前 FC2 路径与资源预算，提出一个有明确收益和停止条件的小试验；未经新的工作安排不要修改推荐 RTL，也不要重跑历史失败方案。向用户用清楚中文报告结果、验证范围和是否值得继续。
