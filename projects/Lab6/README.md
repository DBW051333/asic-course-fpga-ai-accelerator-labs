# Lab6 三层网络逐层截位实验

本工程在已完成的 Lab5 三层全连接工程上实现。Lab5 原工程保留在 `/home/ding/vivado_project/Lab5`。Lab6 沿用其 FC1 乘加流水线、控制器、权重、偏置和层间打包方式，把每层完成乘加、加偏置及激活后的输出截为有符号 8 位或 4 位，并将层间 BRAM、FC2/FC3 输入和乘法器同步改为该位宽。

## 截位方案

| 方案 | FC1 | FC2 | FC3 | 最终准确率 |
|---|---|---|---|---|
| Lab5 未截位 | 32 位 | 48 位 | 64 位 | 37/42 = 88.10% |
| Lab6 8 位 | `[17:10]` | `[16:9]` | `[15:8]` | 37/42 = 88.10% |
| Lab6 4 位 | `[17:14]` | `[11:8]` | `[12:9]` | 36/42 = 85.71% |

截位采用有符号二进制位选择，相当于算术右移后存储低 8/4 位。FC1、FC2 在 ReLU 后截位，FC3 在加偏置后截位。每层先以完整乘加宽度计算，再进行一次截位。FC2/FC3 继续使用原模型的 8 位偏置。截位位置根据 42 个样本的逐层实际范围确定，同时计入上一层的缩放。当前位宽和位置对这 42 个样本均无溢出；若输入分布改变，应重新检查范围。

课程 PPT 第 6 页的“dim0 与 dim1 对应标签”与提供的 `分类结果/int8_results.txt` 相反。本工程沿用后者以及 Lab5 的 FC3 参考结果：`score0 < score1` 判为标签 1，否则判为标签 0。未截位准确率 37/42 与该文件一致。

## 工程和复现

- [8 位 Vivado 工程](vivado8/Lab6_8.xpr)
- [4 位 Vivado 工程](vivado4/Lab6_4.xpr)
- [顶层 RTL](rtl/lab6_top.v)，位宽参数 `WIDTH=8` 或 `WIDTH=4`
- [42 样本测试平台](tb/tb_lab6_top.v)，逐项检查 FC1、FC2、FC3 输出
- [8 位仿真结果](results/rtl_8.csv)，[4 位仿真结果](results/rtl_4.csv)
- [8 位运行记录](results/vivado_8.log)，[4 位运行记录](results/vivado_4.log)

重新生成测试数据及整数参考：

```sh
python /home/ding/vivado_project/Lab6/tools/reference_model.py
```

重新生成 Vivado 工程并运行 XSim：

```sh
/vivado/2025.2/Vivado/bin/vivado -mode batch -source /home/ding/vivado_project/Lab6/tools/create_lab6_project.tcl -tclargs 8
/vivado/2025.2/Vivado/bin/vivado -mode batch -source /home/ding/vivado_project/Lab6/tools/create_lab6_project.tcl -tclargs 4
```

两次 XSim 均运行了全部 42 个样本，FC1/FC2/FC3 每个输出都与独立整数参考一致，`mismatches=0`。4 位方案相对未截位方案多错分样本 34。不过，4 位输出在 27 个样本上出现两类分数相等（其中 21 个标签为 0）；上述准确率采用“相等时判为标签 0”的约定，因此不能只看 36/42 就认为分类信息基本保留。8 位方案没有分数相等的样本。这里验证了行为仿真和准确率，未进行板上测试或资源利用率综合。
