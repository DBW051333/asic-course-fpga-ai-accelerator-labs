# ASIC 课程设计：基于 FPGA 的 AI 加速器设计（Lab1–6）

课程名称依据配套《ASIC课程项目报告模板》中的“ASIC课程设计报告”，项目名称依据 Lab1 课件“基于 FPGA 的 AI 加速器设计”。

备份日期：2026-10-08。保存各 Lab 原版与有代表性的阶段成果、课程原始数据和课件，按原目录名对应工程。

## 代表版本

| Lab | 工程目录（位于 `projects/`） | 保存理由 |
| --- | --- | --- |
| Lab1 | `Lab1`、`Lab1_re` | 基础工程与后续 PS/DMA 集成阶段 |
| Lab2 | `Lab2_4_to_1`、`Lab2_8_3_encoder` | 多路选择器、编码器两项基础实验 |
| Lab3 | `Lab3_sync_fifo`、`aync_fifo` | 同步与异步 FIFO；保留原拼写 |
| Lab4 | `Lab4`、`Lab4_tree4_1221_full4p3` | 课程原版与最终四级加法树优化版，代表优化版通过周期 4.3 ns |
| Lab5 | `Lab5`、`Lab5_optimization/stream_pair256_burst_exact23_tree7_clk4p8` | 课程原版与未截位流式优化版；后者最终结果采用 5.26 ns，不能把目录名 4.8 当成通过周期 |
| Lab6 | `Lab6` | 课程 8 位/4 位量化参考实现 |
| Lab6 资源较省版 | `Lab6_architecture_trials/fc2_interleaved_split11` | 174 拍 × 4.09 ns = 711.66 ns，LUT 15782、DSP 220 |
| Lab6 高并行版 | `Lab6_growth_trials/fc1_128x6_dual` | 135 拍 × 4.91 ns = 662.85 ns，LUT 35323、DSP 220 |

Lab6 三版本的指标、数值校验及验证范围见 [对比说明](course_materials/Lab6三个版本资源与性能对比.md) 和 [机器可读结果](projects/Lab6_three_version_comparison/comparison.json)。历史交接文档中的“当前最佳”可能已经被后续版本更新，以最新对比和对应工程报告为准。

## 资料和依赖

- `course_materials/`：Lab1–6 课件、指导书、原始输入、模型参数、参考输出、分析记录和最终文档。
- `projects/`：上表代表工程的 RTL、TB、约束、IP 配置、XPR、数据、构建/验证脚本与报告；并保留 4 个代表优化版的最终布线 DCP。
- `projects/Lab5_optimization/data` 等共享目录：选中工程引用的公共数据和工具，仅作为依赖，不作为额外的阶段版本。
- `projects/Lab6_three_version_comparison/`：三版本对比与原版独立测量的说明、脚本和报告。
- `manifests/selection.json`：所选代表版本、共享依赖与最终 DCP 清单。
- `manifests/files.json`：备份文件与原文件的路径、大小、SHA-256。

未选入其余试验版本、安装程序、重复原始 ZIP、Vivado 缓存、自动生成的 IP HDL、大型波形和中间检查点。本地原工程未修改，原始数据与课件逐文件保留。

## 获取和校验

```bash
git clone git@github.com:DBW051333/asic-course-fpga-ai-accelerator-labs.git
cd asic-course-fpga-ai-accelerator-labs
python3 tools/verify.py
```

校验脚本核对清单中的每个文件，也检查没有缺失或额外的课程/工程文件。

## 恢复与复现

`projects/` 内保持原工程相对布局；代表工程之间的数据与脚本依赖一并保留。已有文件中部分引用仍为 `/home/ding/vivado_project/` 和 `/home/ding/桌面/Lab/` 的绝对路径，换机器时应把路径改为实际恢复位置。先在新的工作副本中调整，避免覆盖现有工程。

打开 XPR 后，缺少的 IP 输出需要由保留的 XCI/BD 重新生成，再运行仿真或实现。最终优化版还保留对应 Tcl、时序约束、数值/时序报告与布线 DCP。供历史比较或其他试验生成使用的脚本可能引用未选入的旧候选；本备份只覆盖上表代表版本，不提供整个试验搜索目录。

本次验证文件完整性；没有重新运行功能仿真、综合/实现或上板。已有报告中的验证边界继续适用。
