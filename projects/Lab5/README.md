# Lab5 三层全连接工程

工程位置：`/home/ding/vivado_project/Lab5/vivado/Lab5.xpr`

## 结构

Lab5 按课件要求使用三个独立的全连接层，不复用 FC 计算模块：

| 层 | 输入/输出通道 | 数据位宽 | 并行方式 | 激活 |
|---|---|---|---|---|
| FC1（Lab4 `fc.v`） | 512 / 128 | 8 位输入，32 位输出 | 128 路，4 组 | ReLU |
| FC2（`rtl/fc2.v`） | 128 / 32 | 32 位输入，48 位输出 | 32 路，4 组 | ReLU |
| FC3（`rtl/fc3.v`） | 32 / 2 | 48 位输入，64 位输出 | 32 路，1 组 | 无 |

FC2 和 FC3 分别使用自己的乘法器阵列与加法树：

- `fc2_mult_array.v`、`fc2_adder_tree.v`
- `fc3_mult_array.v`、`fc3_adder_tree.v`

FC1 的 128 个输出每 32 个打包为一条 1024 位数据，供 FC2 分 4 次读取。FC2 的 32 个 48 位输出打包为一条 1536 位数据，供 FC3 一次读取。各层计算结果均保留完整位宽，不做截位。

## 仿真结果

XSim 行为仿真已通过：

- FC1：128 个输出全部匹配 `data/reference/fc1.txt`
- FC2：32 个输出全部匹配 `data/reference/fc2.txt`
- FC3：2 个输出全部匹配 `data/reference/fc3.txt`

仿真输出保存在 `results` 目录。重新创建工程并运行仿真：

```text
/vivado/2025.2/Vivado/bin/vivado -mode batch -source /home/ding/vivado_project/Lab5/tools/create_lab5_project.tcl
```
