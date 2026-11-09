# Lab8 完成与基线结果

2026-10-09。本机实现与验证完成；用户说明板卡目前未连接，上板验证待进行。

工程：[Lab8.xpr](/home/ding/vivado_project/Lab8/vivado/Lab8.xpr)。

[说明与上板步骤](/home/ding/vivado_project/Lab8/README.md)、[实现与验证报告](/home/ding/vivado_project/Lab8/docs/Lab8实现与验证报告.md)、[结果JSON](/home/ding/vivado_project/Lab8/results/summary.json)、[PYNQ部署包](/home/ding/vivado_project/Lab8/deploy/lab8_pynq_z2.tar.gz)。

以已优化Lab7交付版独立复制，保留CE、预取、共享BRAM及计算核心；原Lab7源码/数据哈希核对未变。增加64位AXIS包校验与恢复、AXI-Lite统计/软件复位、完整PS/HP0/GP0/DMA系统和Python42样本程序，已生成BIT/HWH/XSA。

AXIS/AXI-Lite回归48份、7776项及50次特征回读通过；实际AMD AXI DMA模型与NPU集成仿真42份、6804个特征值通过，1和162字节的DMA返回包检查通过。PS驱动与报告程序5项本机模拟传输测试通过。均不能当作板上测试。

整机100MHz：计算175拍=1.75us；LUT27193、FF50540、BRAM36等效72、DSP220；WNS+0.495ns、WHS+0.012ns、WPWS+3.750ns，TNS/THS/TPWS均0，路由错误0，DRC无Error/Critical Warning。初次控制CE被自动提升至BUFG产生DPBU-1警告，限制控制网络CLOCK_BUFFER_TYPE NONE后重做实现，最终该警告0。

准确率数值基线37/42（88.095%），真实PS端到端时间待上板。默认活动功耗估算1.470W；仅NPU RTL活动注入估算2.261W，直接映射10%，含X状态和复位概率提示，均非实测且不能与旧Lab7不同负载报告直接比较。

整体层极值满足课件范围，但若要求逐样本每层达到幅值阈值，当前固定移位只有4/42、1/42、12/42满足，应列为后续量化研究问题。课件得分比较方向与提供脚本有差异，数值规则仍沿用已验证Lab7，0异常/1正常仅为课件标签文字的显示映射。

本轮不自动追加优化，先以此为可上板基线。下一步连接板卡取得42样本真实结果与三种时间，然后由用户与Codex一起决定通信、频率、缓冲、量化或资源功耗优化。
