# Lab6 快速 FC2 优化结果

日期：2026-10-06。本轮按用户要求在本机同时比较两个小改动，综合/布线各配置最多 8 个线程，保留原推荐工程。

## 结果

最新已验证最快候选为 **quick_fc2_rom_pipe：171 拍 × 4.30 ns = 735.30 ns**，比 741.20 ns 快 **0.796%**。启动间隔从 562.44 ns 降为 554.70 ns，改善约 1.376%。本轮完成后停止，没有追加新试验。

| 方案 | 拍数 | 最终通过周期 | 总延迟 | 相对原延迟 | LUT | FF | BRAM | DSP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 原推荐 prepack_banked_lookup | 170 | 4.36 ns | 741.20 ns | 基线 | 15755 | 35454 | 68 | 220 |
| FC2 增加一级输入流水 | 171 | 4.30 ns | **735.30 ns** | **快 0.796%** | 15734 | 35596 | 68 | 220 |
| 保留 FC2 权重寄存器映射 | 170 | 4.88 ns | 829.60 ns | 慢 11.927% | 15750 | 35764 | 68 | 220 |

第二个方案的 4.4 ns 原目标未通过，表中 4.88 ns 是布线后调宽约束至 setup/hold 均通过的比较周期，不能将实现脚本返回 passed 理解为达到了 4.4 ns。

## 改动与验证

新增流水版只修改 FC2 的权重/数据流水及相应 valid、first、last 延迟，保持权重、偏置、8 位量化和移位 10/9/8、floor/wrap 分类参考不变。综合将新增权重流水吸收进 DSP，FC2 BRAM 输出寄存器仍为 0；并非已经启用 BRAM 输出寄存器。收益为本次整体综合和布局布线的实测结果，不保证改变一个寄存器在其他实现中可重复获得相同收益。

两个候选初始 RTL 仿真均通过 48 个重叠请求、7776 项分层数值及地址检查，错误 0，课程分类 37/42、平局 0。新增流水版又在最终 **4.30 ns** 时钟下复验，同样通过，并重新打开保存的 routed DCP 检查 setup/hold。

新增流水版 WNS +0.001 ns、WHS +0.013 ns、TNS/THS/TPWS 为 0、WPWS +0.416 ns、布线错误 0。最终最差 setup 路径变为 FC2 product_r 到 acc，数据路径 4.275 ns（逻辑 2.812 ns、布线 1.463 ns）。这些是 RTL 仿真与静态时序结果，没有门级仿真或上板验证。

## 文件入口

- 新最快候选：`/home/ding/vivado_project/Lab6_limit_search/quick_fc2_rom_pipe/`。
- 修改 RTL：上述目录 `rtl/fc_stream_pair_output.v`。
- 最终检查点：`results/final_routed.dcp`；对应约束 `results/final_clock.xdc`（4.30 ns）。
- 布线资源和时序：`results/utilization_impl.rpt`、`timing_final.rpt`、`timing_verified.rpt`、`route_status.rpt`。
- 最终时钟仿真：`results/final_verify_console.log`；脚本 `tools/run_final_verify.tcl`。
- 选中记录：`/home/ding/vivado_project/Lab6_limit_search/results/quick_fc2_selected.json`。
- 本轮全部结果：同目录 `quick_fc2_results.json`、预算 `quick_fc2_trial_plan.json`。
- 旧推荐 `recommended/` 和 `results/recommended.json` 保留原 741.20 ns 内容，尚未覆盖；目录名和旧 JSON 不会自动指向新候选。

## 判断

本轮获得小幅改善，资源没有超预算。收益低于之前约定的 1% 明显延迟改善门槛，按停止要求结束这一轮。若之后另行继续，先针对新关键路径重新预算；不要沿用“RAM 到 DSP 是当前最差路径”的旧判断，也不要重新扩大倍频或 512 路试验而跳过资源、时序评估。
