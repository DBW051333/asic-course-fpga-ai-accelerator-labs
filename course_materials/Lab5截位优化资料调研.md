# Lab5 / Lab6 截位后硬件优化资料调研

调研日期：2026-10-06。只做资料调研及预算，不启动新综合或实现。

## 项目基线与约束

根据本地《Lab6持续优化记录》和 recommended/rtl：器件 xc7z020clg400-1；第一层 256 个配对乘法通道，分两组覆盖输入；每通道计算共享输入的两个权重乘积。当前最快记录 170 拍 × 4.36 ns = 741.20 ns，LUT 15755，FF 35454，BRAM 68，DSP 220（第一层 200，第二层 16，第三层 4）。这些是已有工程结果，非本次新增测量；内部时序通过不等于已上板验证。

现有逐层规则：8 位输出、移位 10/9/8、ROUND=0、SAT=0。保持参考结果的优化要保留截位回绕语义。ReLU 在宽结果上执行后，8 位截位可能回绕成负数，因此不能直接把后层激活解释为无符号数。

512 路路线已因进位链容量、布局压力而停止。用户要求先预算资源；连续没有明显收益时停止。

## 方法对照

以下适用性和优先级是针对本项目的推断，论文结果不等于本项目收益。

| 方法 | 资料中的做法 | 对我们设计的判断 |
|---|---|---|
| 1. DSP 倍频复用 | DSP 运行在主时钟两倍频率，每主周期接受两组运算 | 最值得先预算；保持现有 INT8 运算。需要相位确定的相关时钟、输入选择、结果重组及完整时序约束。[DSP48E1 研究论文](https://wrap.warwick.ac.uk/id/eprint/74989/7/WRAP_fpt2015-ronak.pdf) |
| 2. 输入/输出并行度重分配 | FINN 分别控制输入 SIMD 和输出 PE，允许两维折叠 | 中高优先级：比较少一些输入通道、多一些输出通道；总乘法吞吐相近时，小树与局部布线可能更容易实现。不是保证减少延迟。[FINN RTL 架构](https://xilinx.github.io/finn/2021/09/17/finn-matrixvector-rtl.html) |
| 3. 同频分时复用 | 增加每个乘法器的重复使用次数 | 可明确省 DSP，但增加计算周期。适合作为面积优先版本；速度是否提高取决于时钟提升是否补偿新增周期。[hls4ml 层参数](https://fastmachinelearning.org/hls4ml/ir/attributes.html) |
| 4. 乘加一起映射到 DSP | 利用乘法器后方 ALU、寄存器及级联连接 | 比只省乘法器更完整；我们此前打包累加原型未超过基线，新的结构才值得再考虑。[AMD 算术推断指南](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Coding-for-Optimal-DSP-and-Arithmetic-Inference) |
| 5. DSP 完整流水 | 使用输入、乘积、输出内部寄存器 | 是倍频路线的必要检查项。要核实综合后寄存器是否实际进入 DSP，而非仅在 RTL 中增加延迟。[UG479](https://docs.amd.com/api/khub/documents/gu4oRPFEh_Pm2uaAlfY6Kg/content) |
| 6. 精确范围推导及位宽缩减 | 用权重和量化器做区间传播，删除多余位 | 数值风险较低；现有 FC2/FC3 已做 21/19 位累加，后续重点是逐通道、逐树节点。不能仅凭 42 样本的最大值证明所有输入安全。[hls4ml BitExact](https://fastmachinelearning.org/hls4ml/advanced/precision.html) |
| 7. 存储组织匹配运算 | 合理选择 BRAM/LUTRAM、地址和输出流水 | 已经取得收益，剩余空间有限。倍频时可考虑主时钟宽读、快时钟分两次送入 DSP；带宽需求不会随 DSP 数量减半。[AMD RAM 指南](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Performance-Considerations-When-Implementing-RAM) |
| 8. 局部地址与控制分发 | 复制高扇出驱动寄存器，让逻辑靠近负载 | 作为新结构的配套手段；已有分块 ROM 和物理优化不应无目的重复。[AMD 高扇出优化](https://docs.amd.com/r/2023.1-English/ug949-vivado-design-methodology/Optimizing-High-Fanout-Nets) |
| 9. 固定权重公共子表达式 | 共享常量矩阵中的重复计算 | 先统计零权重、重复权重及可共享组合；若权重逐拍变化，专用固定系数电路可能失去复用优势。不是用通用 LUT 乘法补足并行度。[常量矩阵 CSE 论文](https://arxiv.org/abs/2303.16106) |
| 10. 混合精度及量化训练 | 按层或更细粒度选择位宽，通过训练控制误差 | 需要改变模型/参考规则，不能直接计为当前课程模型的等价优化；若开放模型修改才值得单独研究。[HGQ2](https://fastmachinelearning.org/hls4ml/advanced/hgq.html) |
| 11. 结构化剪枝与权重共享 | 按实际 FPGA 资源目标剪掉结构、共享权重 | 需要重训或调整模型；非结构化零权重不会自动缩短固定拍数。[资源感知剪枝论文](https://arxiv.org/abs/2308.05170)、[hls4ml 优化 API](https://fastmachinelearning.org/hls4ml/advanced/model_optimization.html) |
| 12. 更密集打包 / Overpacking | 更低位宽算术打包，或允许结果字段重叠误差 | 暂不选。现有 INT8 已做共享输入双乘积；论文常用 DSP48E2，精度和端口宽度都要重新核算，近似打包不保持现有结果。[DSP-Packing 论文](https://arxiv.org/html/2203.11028v1) |

## 倍频复用预算：148 个 DSP 有条件成立

当前第一层 256 个通道，每通道两次 INT8 乘法，即每主周期 512 次乘法。200 个通道使用 DSP，56 个通道由 LUT 实现。

若每个 DSP 每快周期完成一次配对乘法，快时钟是主时钟的两倍，则每 DSP 每主周期可接受四次 INT8 乘法：第一层需求 512/4=128 个 DSP；后两层保留 16+4，合计 148，比当前减少 72 个，约 32.7%。这是吞吐预算，未包括可能为其他算术分配的 DSP。

按当前 4.36 ns 主周期，主频约 229.36 MHz，快频约 458.72 MHz。不能凭 DSP 本身速度保证带选择器、路由、结果重组的整体通过。论文中的器件是 Virtex-6，不能把论文频率作为 Zynq-7020 的实测值。

若主时钟降到 200 MHz，周期为 5 ns；保持 170 拍时总时间变为 850 ns，比当前慢。要在这个主频下超过 741.20 ns，最多 148 拍；按原讨论至少 1% 的明显收益条件，最多 146 拍。额外快时钟流水延迟也要计入端到端拍数。

第一层预打包权重每主周期读出 256×25=6400 bit。128 个 DSP 的倍频输入可将其拆成两个 3200 bit 时隙；依然需要同等总带宽。可在主时钟 BRAM 读取后锁存两份权重，再用快时钟选择，具体 BRAM 数量需要按深宽映射核算，不能简单除以二。

论文报告的平均 DSP 减少 39%、LUT 增加 19%、寄存器增加 7%，来自其基准集；只说明存在附加开销，不应用这些比例预测我们的工程。

## 输入/输出并行度预算

FINN 的计算周期近似为 ceil(Nin/SIMD) × ceil(Nout/PE)，不包含填充、排空和访存停顿。其文档要求矩阵宽、高分别能被 SIMD、PE 整除。[折叠约束](https://finn.readthedocs.io/en/latest/reference/folding-constraints.html)

把输入并行度减半、输出并行度加倍，在维度整除且相同运算吞吐条件下，计算周期可近似保持；树变短，局部累加器变多，输入广播和权重布局也会改变。必须与第一层输出顺序、第二层能否持续接收数据一起预算。FINN 中的 SIMD 表示输入运算并行度，与 DSP48E1 的 USE_SIMD 属性不是同一个概念。

## 不应直接套用的结论

1. DSP48E1 是 25×18 乘法器；DSP48E2 是 27×18。WP487 针对 UltraScale/UltraScale+ 的打包点积，不能复制其间隔与累加长度到 E1。[WP487](https://docs.amd.com/api/khub/documents/Wr7TqDp2Zv68IugmRp9hwg/content)
2. DSP48E1 的 TWO24、FOUR12 是加减法 SIMD；启用这两个模式时乘法器必须禁用，不能据此获得两路或四路乘法。[UG953](https://docs.amd.com/r/2024.1-English/ug953-vivado-7series-libraries/DSP48E1)
3. 对每项乘积先右移再求和通常不等价于求和后右移：例如移位一位，1+1 最终得到 1，但分别移位后得到 0。若提前丢低位，必须处理低位累计产生的进位。
4. 改饱和或四舍五入会改变当前 SAT=0、ROUND=0 参考行为；需要单独标成模型规则修改。
5. 少拍数或少资源都不能单独证明更快；比较端到端延迟，并独立列出连续输入的请求间隔。

## 建议讨论顺序

先做倍频 DSP 单元的纸面时序和资源预算；同时比较输入/输出并行度重分配的两三个结构。保持现有权重与量化规则，再检查局部位宽、权重数据组织和控制扇出。现有加法树及物理优化路线已有充分记录，不继续重复微调。INT4、剪枝、近似乘法只作为允许修改模型时的后备方向。

本次未更改 RTL、未运行综合或布线。所有新方案收益均待验证。
