# Lab8 FC2累加结构优化结果

2026-10-11。根据聊天“Lab8方向与指南”的最新建议，从`fc1_192_tree_retimed`独立派生`fc2_192_single_acc`，源基线仍为`lab8_128_resource_v1`。**整机FF减少10.88%，保持原仿真性能，完整实现和部署包校验通过。** 默认入口仍为`fc1_192_batch_integrated`，双基线和父候选保留，未迁移AX7020。

[独立工程与复现](/home/ding/vivado_project/Lab8_optimization_trials/fc2_192_single_acc/README.md) · [实验记录](/home/ding/vivado_project/Lab8_optimization_trials/fc2_192_single_acc/experiment.json) · [完整汇总](/home/ding/vivado_project/Lab8_optimization_trials/fc2_192_single_acc/results/summary.json) · [部署包](/home/ding/vivado_project/Lab8_optimization_trials/fc2_192_single_acc/deploy/lab8_fc2_192_single_acc.tar.gz)

## 口径与预算

本轮主目标是相对最新直接父版整机21212 FF减少至少5%：至少省1061个，验收≤20151。保持FC1 192路、全DSP乘法、同一重新量化模型、142.857132 MHz单PL时钟、DSP212、BRAM36等效56；LUT增长预算≤3%，Slice不增加，核心216拍与启动间隔172拍不退化。先用同边界FC2小原型验证7ns时序和净资源潜力，再做完整系统。最多两种小原型、两次初始完整实现；实际一条结构、一次完整构建，条件式物理修复记录如下。

## 改动及正确性

唯一功能RTL变化为[fc_stream_pair_output.v](/home/ding/vivado_project/Lab8_optimization_trials/fc2_192_single_acc/rtl/core/fc_stream_pair_output.v)：将FC2奇偶双累加器、分段低/高位加法和最后归并替换为单套21位反馈累加器。

DSP权重、输入、乘积流水和乘法表达式保持原样。首项从bias初始化，此后每个有效乘积加入同一acc；最后一项同拍将next_sum写入snapshot。保留snapshot以避免下一样本开始累加时覆盖上一样本尚未发完的结果。输出前保留三个CE控制延迟位，与父版的归并/快照启动时刻对齐，因此FC2的valid、四路数据、地址和done逐拍相同。

固定模型所有合法INT8输入下，任何部分和加bias的保守绝对界为827962，小于有符号21位上限2^20；不是仅用课程样本的观测值缩窄位宽。新旧累加都是相同整数和，CE暂停同时冻结算术与控制；复位清有效控制，首个有效输入重新初始化旧acc。数学论证与仿真见[周期模型](/home/ding/vivado_project/Lab8_optimization_trials/fc2_192_single_acc/results/fc2_cycle_model.json)、[等价记录](/home/ding/vivado_project/Lab8_optimization_trials/fc2_192_single_acc/results/fc2_equivalence.json)，没有声称形式化模型检查。

## 原型与整机结果

同配置、同输入输出寄存边界、同7ns约束的FC2原型：FF 4797→2201，省2596；DSP均16，内部AREG/BREG/MREG/PREG配置相同。新版WNS +1.568ns，WHS +0.129ns。顶层外部IO未表征，仅用来评估内部寄存路径，不替代完整系统。原型推算整机FF减少12.24%，**最终采用下面的实际整机减少率，不把原型推算当交付结果。**

| 指标 | 最新父版 | 新候选 | 减少率 |
|---|---:|---:|---:|
| LUT | 14647 | 14328 | 2.18% |
| FF | 21212 | 18905 | 10.88% |
| Slice | 6218 | 5993 | 3.62% |
| BRAM36等效 | 56 | 56 | 0.00% |
| DSP | 212 | 212 | 0.00% |

完整保存DCP重新打开核查：WNS +0.015ns、WHS +0.052ns，单条7nsPL时钟，所有可布线网络完成，错误/严重警告DRC为0。FC1/FC2/FC3的DSP分别192/16/4，全部使用乘法，内部寄存配置与直接父版相同。FC2网表有1592个FF，旧奇偶累加、分段归并和parity_local已移除；单acc和必要snapshot仍存在。[最终检查点](/home/ding/vivado_project/Lab8_optimization_trials/fc2_192_single_acc/results/checkpoint_verified.json)、[FC2网表审计](/home/ding/vivado_project/Lab8_optimization_trials/fc2_192_single_acc/results/fc2_register_audit.json)

首轮路由WNS -0.196ns、WHS +0.052ns；是否执行条件式物理修复：1。修复仅按既有流程进行物理优化与重布线，没有更改RTL、7ns时钟、false path或multicycle约束。原始路径和报告保留。[实现记录](/home/ding/vivado_project/Lab8_optimization_trials/fc2_192_single_acc/results/implementation_history.json)

性能保持：核心216拍/1.512 μs；批量II172拍；实际AMD DMA IP、同一带停顿AXI内存模型的42样本双方均7423拍/51.961 μs。没有新增性能加速，资源收益不等于同幅度节能。

## 验证与证据范围

- FC2旧/新RTL逐拍对照198帧、6336个完整23位结果，覆盖原48种激活、INT8极值、16随机输入，连续/类FC1/随机valid，6338次CE暂停和中途复位；同时与独立整数参考核对。
- 独立标量参考48样本/7776值，集成RTL48任务及94批量样本/15228值；长输出反压、满8信用、异常帧、软复位与特征回读保持原覆盖。
- 真实DMA父/候选各42样本/6804值、signed scores、长度、TLAST/TKEEP、越界哨兵与末样本162字节特征；额外真实DMA错误回复与恢复通过。
- FC1全精度66输入/8448值、随机CE暂停；另66输入/8448值覆盖暂停期间并行写下一银行与切换。7项主机检查、0/超限批量及16383最大协议/驱动边界通过，没有完整16383样本仿真。
- 完整系统综合/布局布线、最终DCP、时钟/DRC/路由和DSP寄存器审计；父版/default/双基线及当前入口校验保护，模型和PS驱动未变。bit/hwh/xsa来自同次构建，部署归档逐文件校验。[保护记录](/home/ding/vivado_project/Lab8_optimization_trials/fc2_192_single_acc/results/source_integrity.json)、[部署包校验](/home/ding/vivado_project/Lab8_optimization_trials/fc2_192_single_acc/results/package_verified.json)

**未上板、未测真实API与功耗。** PYNQ-Z2预设DDR负DQS skew警告沿用父版，PS配置未修改；PL实现检查不能替代DDR板测。所有时间均为仿真或工具报告，不是AX7020/PYNQ-Z2实测。

## 指定基线与后续使用

指定128资源基线核心303拍，直接父版与新候选均216拍；既有核心时间减少28.71%不是本轮新增收益。新候选与128基线的资源差为：

| 资源 | 128基线 | 新候选 | 差值 |
|---|---:|---:|---:|
| LUT | 11720 | 14328 | +2608 |
| FF | 28109 | 18905 | -9204 |
| Slice | 6444 | 5993 | -451 |
| BRAM36等效 | 40 | 56 | +16 |
| DSP | 148 | 212 | +64 |

未对指定128/256基线做本轮同窗口DMA对照，不宣称对应的批量加速。建议保留这个已验证资源候选，默认入口保持原样。进一步优化先评估具体收益，板侧使用前按README完成分类、特征、异常恢复验证，再运行同版本API计时脚本。
