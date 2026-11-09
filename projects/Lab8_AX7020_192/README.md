# Lab8 AX7020 192路移植工程

2026-10-11，从 `Lab8_integrated_192` 独立派生，源基线 `lab8_128_resource_v1`。保持重新量化模型、FC1 192路全DSP和统一约142.857132 MHz PL时钟。来源、双基线、smoke与默认入口均保留。

目标为 AX7020 / xc7z020clg400-2，使用已经通过smoke的AC7020社区板卡PS预设：33.333333 MHz参考、32位1 GiB DDR、UART1。MM2S/S2MM地址解码覆盖0–0x3FFFFFFF。

Vivado工程：`vivado/Lab8.xpr`。构建：

```bash
/vivado/2025.2/Vivado/bin/vivado -mode batch -source tools/build.tcl -tclargs all
/vivado/2025.2/Vivado/bin/vivado -mode batch -source tools/verify_checkpoint.tcl
```

板上从部署目录使用镜像已验证的PYNQ解释器：

```bash
sudo bash -lc 'cd /home/xilinx/jupyter_notebooks/Lab8_AX7020_192 && /usr/local/share/pynq-venv/bin/python acceptance.py'
```

程序在加载Overlay后核查真实PLL/FCLK分频与NPU tick；不会修改PLL或启动系统。PL周期耗时按寄存器推算频率换算；此项不是仪器测量。DMA缓冲区逐次检查在1 GiB解码范围内。

验证状态以 `migration.json`、`results/summary.json` 和板测原始文件为准。源工程历史证据在 `evidence/source`，不能当作本工程结果。完整16383批量与功耗尚未实测。

部署XSA名为`lab8_ax7020_192.xsa`。PYNQ 3.0.1会将与bit同名的XSA旁文件判为XSA输入，因此运行目录保持`lab8.bit`/`lab8.hwh`同名配对，XSA用独立名称。三者仍来自同一次目标构建。

## 已完成的最终验收

仿真、完整目标实现、最终DCP重开检查及真实板上验收均通过。WNS +0.229 ns，WHS +0.026 ns；LUT14299、FF18905、Slice5791、BRAM36等效56、DSP212。

板上42/42分类、6804逐层值、N=1/3/8/16/42/48/128连续批量、截断包/复位/重载恢复通过。实际高DDR地址0x380xxxxx可达。寄存器及tick核查FCLK0约142.857141 MHz；核心216拍约1.512 μs。

每组预热10次、测量100次：单样本完整API中位数1.832 ms，42样本批量3.320 ms（约12651样本/s），128样本批量4.834 ms（约26478样本/s）。完整报告见[板测报告](results/board_report.md)，部署包内为board_report.md；原始数据在results/board。

当前板测使用既有启动系统，未部署XSA的PS初始化；社区预设保留smoke同样的DDR DQS警告。未测功耗、全DDR压力或16383样本完整批量。
