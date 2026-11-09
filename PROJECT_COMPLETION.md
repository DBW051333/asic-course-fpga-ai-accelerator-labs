# Lab项目结项：标志版本归档

2026-11-09结项。按用户要求，仅补充下列标志版本与必要资料，保留仓库原有Lab1–Lab6工程和历史。本次未新增仿真、实现、板测或功耗测量。

| 标志版本 | 入口 | 已有结果与验证范围 |
| --- | --- | --- |
| 默认192路AX7020板测版 | [Lab8_AX7020_192](projects/Lab8_AX7020_192/README.md) | 约142.857MHz统一PL时钟，FC1 192路、DSP212；有真实板测，默认选择未变 |
| 软件优化完成版 | [PS API v3](projects/Lab8_AX7020_trials/ps_api_v3/README.md) | 同轮42样本完整API中位数1.588→1.378ms，减少13.21%；真实板测42/42课程样本正确、6804逐层值一致，持续测试和DMA错误恢复通过 |
| 统一提频实验版 | [platform v1](projects/Lab8_AX7020_trials/platform_v1/README.md) | 统一166.667MHz，已板测；N4096完整API同轮减少5.67%，N42无测得收益；没有切换默认工程 |
| 最后完成的复用硬件版 | [256路说明](projects/Lab8_AX7020_trials/shared256_hybrid_v1/README.md)、[完整系统](projects/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/README.md) | 三层共享220 DSP＋36路专用软乘法单元；核心200周期，封装软件计数201周期；完整PS/DMA系统实现、DMA-IP仿真及布线后功能仿真完成，未板测 |

四个版本保留RTL、TB、约束、IP配置、权重和参考数据、构建/验证脚本、驱动、Notebook、部署包及结果报告。默认192、提频版和256完整系统保留最终布线检查点。256版的`baseline192/data`仅为模型重排校验所需数据，不包含额外192复用工程。

512路只保留[试验结果](projects/Lab8_AX7020_trials/shared512_hybrid_v1/实验结果.md)及配置/比较JSON：精简版RTL132周期、48样本7776值通过，但未完成布线、全系统和板测；没有上传其候选源码或检查点。其他优化分支源码、历史PPT草稿、工具缓存、大型波形、安装包和系统镜像未新增上传。

## 最终资料

- [最新汇报PPT：v53专用LUT简明讲解](course_materials/Lab8/PPT_系统实现与探索/output/Lab8_专用LUT简明讲解_v53.pptx)：仅保留最新汇报版本；[讲解与纠错记录](course_materials/Lab8/PPT_系统实现与探索/讲解纠错与后续PPT要点.md)用于追溯技术口径。
- [Lab8原课件](course_materials/Lab8/Lab8.pptx)、[Lab7课件](course_materials/Lab7/Lab7.pptx)、Lab8原始模型/输入/参考数据以及阶段结果说明。
- [AX7020改动复盘](course_materials/Lab8/从原始Lab8到最新工程_改动与效果.md)、[软件v3结果](course_materials/Lab8/AX7020_PS_API_v3优化结果.md)、[提频板测结果](course_materials/Lab8/AX7020平台优化v1结果.md)。

保留的原始资料中部分链接指向未选入的历史实验，按来源记录理解；它们不表示这些分支也已上传。本归档以本页四个版本为恢复入口。

## 恢复与校验

```bash
python tools/verify.py
```

[文件清单](manifests/files.json)保存`projects/`与`course_materials/`全部文件的原路径、大小及SHA-256；[本轮选择](manifests/final_2026-11-09.json)列出实际补充文件。原失败试验及136版本记录继续沿用原校验清单。

源码保持原字节，仍可能使用`/home/ding/vivado_project`等Linux绝对路径。恢复时按原路径布置或在独立副本中调整，再按XCI/BD/Tcl生成IP；AX7020构建依赖原环境的Vivado 2025.2和板卡文件。部署包位于各工程`deploy/`。256复用版仅有CMD1单样本和CMD2特征读取，不把192版的批量CMD3能力算到它上面。

核心周期、DMA仿真、PL事务和完整API时间保持各自统计边界；42个课程样本参与过量化选择，不当作独立泛化测试；工具功耗估计不当作板上实测。仓库继续保持私有。
