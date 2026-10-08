# Lab5 优化实验

本轮已完成并收敛。推荐工程：[stream_pair256_burst_exact23_tree7_clk4p8](/home/ding/vivado_project/Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8/README.md)。

[完整优化报告](/home/ding/vivado_project/Lab5_optimization/Lab5三层网络优化报告.md)包含所有已完成的布局布线结果、被舍弃的方案、证明与复现步骤。


## 理论位宽 25 / 40 对照实验（2026-10-05）

已完成独立工程 `stream_pair256_theory25_40_tree7_clk4p8`。内部采用 25 / 40 / 53 位，FC1/FC2 层间接口采用 25 / 40 位。功能及连续运行检查通过，布线后 5.26 ns、168 拍、216 DSP、61 BRAM；LUT 24,412、FF 42,408。相对原推荐版本，速度不变，LUT +468、FF +424。详见 [位宽修改对照结果](stream_pair256_theory25_40_tree7_clk4p8/位宽修改对照结果.md)。


## 后续截位优化（2026-10-05）

在本目录推荐版本基础上，独立完成 20 个 RTL 候选、15 个综合和 9 个完整布线比较。最快的 8 位截位版本为 169 拍、5.04 ns、851.76 ns，保持课程 42 样本的分类和 Lab6 8 位层输出数值。它比本目录未丢失有效数值的版本快约 3.6%。

[完整截位优化报告](/home/ding/vivado_project/Lab5_truncation_optimization/Lab5截位优化对比报告.md)；[推荐截位工程](/home/ding/vivado_project/Lab5_truncation_optimization/recommended/Lab5_truncation_recommended.xpr)。
