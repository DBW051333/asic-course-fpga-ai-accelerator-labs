# AX7020 shared256 完整工程

220 DSP＋36路LUT打包乘法，三层复用，FC1 256路/2组；单bank输入，CMD1单样本推理、CMD2读回162个逐层值。时钟约142.857132 MHz，目标xc7z020clg400-2。模型不变。核心200周期，封装软件可读compute计数201周期。

完整结果见 `results/summary.json` 与上一级 `实验结果.md`。新硬件未上板，仿真和布线不作为实测。512路和批量CMD3本轮未实施。

## 构建

在工程所在位置运行：

```bash
/vivado/2025.2/Vivado/bin/vivado -mode batch -source tools/build.tcl
/vivado/2025.2/Vivado/bin/vivado -mode batch -source tools/verify_final.tcl
python3 tools/run_sim.py axis
python3 tools/run_dma_sim.py
```

RTL的mem路径已绑定本目录；迁移到其他目录时需重写RTL与TB中的绝对路径。构建使用AX7020社区PS预设：33.333333 MHz参考、32位1 GiB DDR、UART1，DMA覆盖0..0x3FFFFFFF。默认板上工程和启动系统未更改。

## 部署文件

`overlay/lab8.bit`、`overlay/lab8.hwh`同名配对，`overlay/lab8_ax7020_shared256.xsa`独立命名，避免PYNQ将同名XSA自动视为Overlay输入。最终压缩包在上一级 `deploy/lab8_ax7020_shared256.tar.gz`。包内bit/hwh、驱动、运行程序和42个测试样本处于同一目录。

在AX7020既有PYNQ镜像解压后，可运行：

```bash
sudo /usr/local/share/pynq-venv/bin/python run_lab8.py --features
```

这会加载新的PL位流并校验42样本分类与6804逐层值；本轮没有实际执行这条上板命令。驱动沿用单样本协议，加入既有AX7020只读FCLK/tick核查与DMA缓冲区1GiB可达检查；不调整PLL或启动系统。软件耗时必须由新板测获得。

`results/power_default_activity.rpt`是Vivado默认活动率估计，不能当作板上功耗。

PS社区预设保留既有DDR DQS负偏斜警告；本轮没有重新验证PS初始化、DDR训练或启动镜像。板上推荐先沿用原镜像加载PL bit/hwh，不能把PL布线通过解释为新PS启动系统已验证。
