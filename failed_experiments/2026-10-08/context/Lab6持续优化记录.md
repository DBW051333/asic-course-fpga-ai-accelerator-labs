# Lab6 持续优化记录

基于已优化 Lab5 延伸的标准 8 位逐层截位设计。器件 xc7z020clg400-1，Vivado 2025.2；原始权重、偏置、移位 10/9/8、逐层输出与分类规则保持一致。独立 Lab6 文件夹和之前的最佳工程保留。

## 当前结果

目前已完成布线的最快候选为 **prepack_banked_lookup**：170 拍 × 4.36 ns = **741.20 ns**；比本轮起点 801.06 ns 减少 **7.47%**。该结果是内部时钟路径的布线时序结果；最终导出和最终周期仿真状态另见 `results/recommended.json`。

## 搜索方向

1. BRAM 读出流水线：增加同层次输出寄存，配套延迟输入和有效标签；允许多一拍，按总时间比较。
2. 精确内部位宽：固定权重下 FC2 所有 INT8 输入及累加前缀在 [-874237,875063]，FC3 在 [-251408,252217]，分别使用 21、19 位累加，保持输出接口位宽。
3. 自由地址计数：无效周期也读取合法地址，用有效流水控制累加，去除空闲保持逻辑对 ROM 地址和使能的影响。
4. 第一层提前打包固定权重：将权重组合加法移到离线生成的 ROM 内容。
5. 提前读取偏置：将偏置与有效标签同步流水，避免末级偏置 ROM 选择与累加相连，不新增拍数。
6. 三输入及混合加法树：分别六级、七级，保持每节点有符号范围，完整保留乘积和进位。
7. DSP 打包累加：在一个 DSP 中累加两个通道，以低 16 位的回绕和乘积符号跟踪低通道进位；恢复两路精确结果。原型校正与恢复同拍形成约 6 ns 路径，新增版本将其拆开并加入偏置流水。
8. 多轮物理优化：收紧目标，比较 AggressiveExplore 和 AggressiveFanoutOpt。
9. 将预打包权重与六级、七级树组合，检查面积减少是否能改善布局。
10. 精确半字节查表：将两个有符号/无符号 4 位交叉乘积改为 256 项分布式 ROM，保持乘法流水拍数。
11. 分块地址计数：16 个独立、同步复位启动的计数器分别读取 16 路权重，降低地址分发扇出；保持总拍数。共享宽 ROM 的多读端口原型导致综合展开和内存耗尽，主动中止；随后将权重内容和 RTL 存储都拆成 16 个独立 ROM。
12. 在独立分块 ROM 上加入偏置流水：综合关键路径由地址转移至偏置选择和累加后，针对新瓶颈继续组合。
13. 保留中央地址寄存器：比较只阻止寄存器吸收到 RAM 的小改法能否接近分块效果、节省 BRAM。
14. 512 路第一层、每拍双输出、第二层双输入：把 DSP 从第一层重新分配为 184+32+4，总数保持 220；其余乘法用 LUT 精确查表。第一层 512 特征九级树、第二层增加双乘积精确求和流水。功能测得 107 拍、请求间隔 65 拍。该全二叉树原型在布局前失败：CARRY4 需要 14014，超过器件 13300。
15. 512 路混合树：前两级三输入、后六级二输入，针对 CARRY4 超容量减少树节点；理论减少一拍，完整精度节点范围证明同步生成。

## 完整阶段记录

| 方案 | 仿真 | 综合 | 布线 | 拍数 | 周期 ns | 总时间 ns | LUT | FF | BRAM | DSP | CARRY4 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| postroute_fanout | inherited_RTL | not_run | passed | 169 | 4.74 | 801.06 | 20075.0 | 40600.0 | 61.0 | 220.0 | 6316.0 |
| bram_pipe | passed | passed | not_run | 170 | — | — | 21749.0 | 39787.0 | 61.0 | 220.0 | 6309.0 |
| narrow | passed | passed | not_run | 169 | — | — | 21494.0 | 35468.0 | 61.0 | 220.0 | 6316.0 |
| bram_pipe_narrow | passed | passed | not_run | 170 | — | — | 21618.0 | 39720.0 | 61.0 | 220.0 | 6309.0 |
| free_address_narrow | passed | passed | not_run | 169 | — | — | 21419.0 | 35470.0 | 61.0 | 220.0 | 6304.0 |
| free_address_pipe_narrow | passed | passed | passed | 170 | 4.56 | 775.2 | 20047.0 | 41353.0 | 61.0 | 220.0 | 6310.0 |
| fc1_prepack_pipe_narrow | passed | passed | passed | 170 | 4.51 | 766.7 | 16544.0 | 39539.0 | 61.0 | 220.0 | 5716.0 |
| phys_bram_register | inherited_RTL | not_run | failed | 169 | — | — | — | — | — | — | — |
| phys_aggressive45 | inherited_RTL | not_run | passed | 169 | 4.58 | 774.02 | 20077.0 | 40600.0 | 61.0 | 220.0 | 6316.0 |
| dsp_packed_mac_narrow | passed | passed | not_run | 170 | — | — | 21561.0 | 39607.0 | 61.0 | 220.0 | 6110.0 |
| free_biaspipe_narrow | passed | passed | passed | 169 | 4.78 | 807.82 | 19998.0 | 41237.0 | 61.0 | 220.0 | 6316.0 |
| ternary6_bias_narrow | passed | passed | passed | 167 | 4.87 | 813.29 | 16245.0 | 36511.0 | 61.0 | 220.0 | 5056.0 |
| hybrid7_bias_narrow | passed | passed | passed | 168 | 5.0 | 840.0 | 16744.0 | 37271.0 | 61.0 | 220.0 | 5212.0 |
| dsp_mac_pipe_bias | passed | passed | passed | 171 | 4.51 | 771.21 | 19785.0 | 41537.0 | 61.0 | 220.0 | 6052.0 |
| phys_aggressive43 | inherited_RTL | not_run | passed | 169 | 4.58 | 774.02 | 20077.0 | 40600.0 | 61.0 | 220.0 | 6316.0 |
| phys_fanout43 | inherited_RTL | not_run | passed | 169 | 4.58 | 774.02 | 20077.0 | 40600.0 | 61.0 | 220.0 | 6316.0 |
| prepack_ternary_bias | passed | passed | passed | 168 | 4.69 | 787.92 | 12806.0 | 35297.0 | 61.0 | 220.0 | 4456.0 |
| prepack_hybrid_bias | passed | passed | passed | 169 | 4.8 | 811.2 | 13290.0 | 36361.0 | 61.0 | 220.0 | 4612.0 |
| dsp_mac_lookup_cross | passed | passed | passed | 171 | 4.55 | 778.05 | 18866.0 | 40974.0 | 61.0 | 220.0 | 5604.0 |
| prepack_phys_explore | inherited_RTL | not_run | passed | 170 | 4.48 | 761.6 | 16543.0 | 39539.0 | 61.0 | 220.0 | 5716.0 |
| prepack_phys_fanout | inherited_RTL | not_run | passed | 170 | 4.55 | 773.5 | 16543.0 | 39539.0 | 61.0 | 220.0 | 5716.0 |
| prepack_address_banks | passed | failed | not_run | 170 | — | — | — | — | — | — | — |
| prepack_banked_rom | passed | passed | passed | 170 | 4.4 | 748.0 | 16578.0 | 35399.0 | 68.0 | 220.0 | 5716.0 |
| prepack_banked_bias | passed | passed | passed | 170 | 4.4 | 748.0 | 16638.0 | 35538.0 | 68.0 | 220.0 | 5716.0 |
| prepack_banked_lookup | passed | passed | passed | 170 | 4.36 | 741.2 | 15755.0 | 35454.0 | 68.0 | 220.0 | 5268.0 |
| prepack_counter_keep | passed | passed | passed | 170 | 4.4 | 748.0 | 16496.0 | 35455.0 | 61.0 | 220.0 | 5716.0 |
| bank_phys_explore | inherited_RTL | not_run | passed | 170 | 4.36 | 741.2 | 16578.0 | 35399.0 | 68.0 | 220.0 | 5716.0 |
| bank_phys_fanout | inherited_RTL | not_run | passed | 170 | 4.36 | 741.2 | 16578.0 | 35399.0 | 68.0 | 220.0 | 5716.0 |
| dual512_lookup | passed | passed | failed | 107 | — | — | 44732.0 | 98499.0 | 135.5 | 220.0 | 14014.0 |
| dual512_hybrid | passed | running | not_run | 106 | — | — | — | — | — | — | — |

尚未布线的资源为综合值，不能与布线后资源直接推断速度。`inherited_RTL` 表示仅改变物理实现，沿用已验证 RTL；最终选中方案会在最终周期重新仿真。

## 数值依据

每个 RTL 候选检查 42 个课程样本及 6 个扩展输入，48 次重叠请求共 7,776 个层输出和地址。全部使用相同整数参考，不通过改变标签或相等规则提高准确率。
打包累加满足 T=(S1<<16)+S0。令 low 为 T 的低 16 位无符号数，q=floor(S0/65536)，则 S0=(q<<16)+low、S1=(T>>16)-q。每个 INT8 乘积的绝对值小于 65536，故单步回绕变化仅为 -1/0/+1，可由乘积符号及 low 的升降精确追踪。首项含偏置的范围在有符号 16 位内，可由符号位初始化 q。固定 FC2 权重的所有前缀 q 在 [-14,13]，5 位足够；packed sum 用 48 位，不发生累加溢出。数学检查另含 16,789,504 个前缀恢复值，并不等同于穷举全部输入向量。
三输入树各节点按所覆盖叶子数量设置位宽；叶子视为任意有符号 16 位值，逐节点范围证明见候选 `data/tree_width_proof.json`。
512 路原型：固定第一层权重、任意独立 INT8 输入，完整向量加偏置在 [-3575930,3574270]，23 位足够。九级树使用逐层 17 至 25 位，保持任意有符号 16 位乘积求和，最后按已证明的固定权重范围传入 23 位。依据见 `dual512_lookup/data/fc1_full_vector_bounds.json`。

## 查阅资料

- [AMD UG949：RAM 性能注意事项](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Performance-Considerations-When-Implementing-RAM)：同层次输出流水和大 RAM 的地址流水指导。
- [AMD UG949：DSP 与算术推断](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Coding-for-Optimal-DSP-and-Arithmetic-Inference)：充分使用 DSP 流水；三输入加法树的资源效率。
- [AMD UG835，Vivado 2025.2：phys_opt_design](https://docs.amd.com/r/2025.2-English/ug835-vivado-tcl-commands/phys_opt_design)：物理优化模式、迭代和寄存器优化。实际工具拒绝布线后的 -bram_register_opt，已保留失败日志，不将文档中通用选项视为所有阶段均可用。
- [AMD UG901：乘加及累加推断](https://docs.amd.com/r/2023.2-English/ug901-vivado-synthesis/Multiply-Add-and-Multiply-Accumulate-Implementation)：DSP MAC 推断依据。

## 限制与停止判断

以相对当前最佳总时间至少 1% 的减少作为明显速度收益；同时记录资源收益。只有在主要结构改法和数轮物理优化均完成比较后，才说明已测试方向暂未见明显空间，不能证明 FPGA 的全局最优解。
通过周期在固定布线结果上按 0.01 ns 网格选取，setup、hold、pulse width 和完整布线均须通过。外部 IO 延迟与引脚未定义、未上板。物理输入 ROM 使用课程样本 1，功能测试通过层次访问更换输入；更改物理初始化需重新综合、布线。
## 日志和交付

- [机器可读对比](/home/ding/vivado_project/Lab6_limit_search/results/comparison.csv)
- [DSP 累加公式检查](/home/ding/vivado_project/Lab6_limit_search/results/packed_mac_math_proof.json)
- [当前最佳布线 DCP](/home/ding/vivado_project/Lab6_limit_search/prepack_banked_lookup/results/final_routed.dcp)
