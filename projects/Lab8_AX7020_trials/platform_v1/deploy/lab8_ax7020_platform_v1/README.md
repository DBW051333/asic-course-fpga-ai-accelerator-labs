# AX7020 platform_v1

从PS API v3独立派生，单PL时钟166.667MHz。实际结果与范围见 [完整报告](results/optimization_report.md)。默认工程未切换。

Vivado：`vivado -mode batch -source tools/build.tcl -tclargs all`；最终DCP：`vivado -mode batch -source tools/verify_checkpoint.tcl`。板端从部署包运行 `acceptance.py`、`compare_api.py`、`stress_api.py`、`fault_dma.py`。CPU767提案未部署，不能用其XSA直接启动Lab8。
