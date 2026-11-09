# AX7020：PS → PL 数据传输交接说明

整理日期：2026-10-24。对象：接手板上模型部署、需要实现 PS/PL 数据交换的 AI 或开发者。

本文依据本机 Lab8 的实际 Python 驱动、RTL 和 Vivado 建图脚本整理。现有示例是小型 INT8 神经网络，并不是已完成的大模型部署。可以复用传输方法；大模型的权重、激活、KV cache 和指令协议需要按新硬件另行定义。

## 1. 先理解数据到底经过哪里

本项目使用 AX7020（Zynq-7020），PS 运行 Linux/PYNQ，PL 放计算模块和 AXI DMA。

```text
控制路径：
PS CPU ── M_AXI_GP0 ── AXI 互连 ── DMA 的 AXI-Lite 控制寄存器
                                └─ NPU 的 AXI-Lite 控制/状态寄存器

发送数据：
PS Python 把数据写入 DDR 中的 DMA 缓冲区
    ↓
AXI DMA 的 M_AXI_MM2S 经 PS S_AXI_HP0 读取 DDR
    ↓
DMA 的 M_AXIS_MM2S ── AXI-Stream ── NPU 的 S_AXIS

接收结果：
NPU 的 M_AXIS ── AXI-Stream ── DMA 的 S_AXIS_S2MM
    ↓
DMA 的 M_AXI_S2MM 经 PS S_AXI_HP0 写入 DDR 接收缓冲区
    ↓
PS 等待完成并处理缓存一致性，然后读取结果
```

MM2S = Memory Mapped to Stream；S2MM = Stream to Memory Mapped。

`sendchannel` 是 PS 发往 PL，`recvchannel` 是 PL 返回 PS。AXI-Lite 主要用来配置和查询；本项目的大块输入不靠 CPU 逐字写 AXI-Lite。

注意：HP0 是 PL 主设备访问 PS DDR 的接口。不能仅凭“PS 往 PL 发数据”就把数据路径接到 GP0；这里真正搬运数据的是 DMA。

## 2. 本机应优先阅读的源码

### 已完成板测的软件优化候选 PS API v2

- 驱动：`/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v2/ps/lab8_driver.py`
- 时钟、DMA 地址可达性检查：`/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v2/ps/ax7020_runtime.py`
- 批量调用：`/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v2/ps/run_batch.py`
- 硬件连接：`/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v2/tools/build.tcl`
- PL 包格式与寄存器：`/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v2/rtl/lab8_npu.v`
- 命令处理：`/home/ding/vivado_project/Lab8_AX7020_trials/ps_api_v2/rtl/lab7_top.v`

重点看 `Lab8NPU.__init__()`、`_exchange()`、`_wait_dma()`、`reset_dma()`、`infer()` 和 `infer_batch()`。

### 默认工程和后续研究分支要区分

- 默认选择记录：`/home/ding/vivado_project/Lab8_baselines/current_project.json`
- 当前默认工程：`/home/ding/vivado_project/Lab8_AX7020_192`
- 默认 PS 源码：`/home/ding/vivado_project/Lab8_AX7020_192/ps/`
- 256 路复用研究版 PS：`/home/ding/vivado_project/Lab8_AX7020_trials/shared256_hybrid_v1/hybrid256/ps/`

PS API v2 是独立软件候选，没有切换默认工程。256 路复用研究版的新硬件未上板，驱动支持 CMD1/CMD2，不能假定支持 v2 的批量 CMD3。512 路研究版未完成全系统与板测。

不要把某一版的驱动、另一版的 bit/hwh 和第三版的命令格式混用。

## 3. 现有硬件的 DMA 配置

以下值来自 PS API v2 的 `tools/build.tcl`，不是所有 FPGA 工程的固定要求。

| 项目 | 当前配置 |
|---|---|
| DMA 实例名 | `axi_dma_0` |
| NPU 实例名 | `npu_0` |
| DMA 模式 | Simple DMA，关闭 Scatter-Gather |
| DMA 地址位宽 | 32 bit |
| MM2S/S2MM 内存接口 | 64 bit |
| 两个 AXI-Stream 接口 | 64 bit，即一拍最多 8 字节 |
| DRE | 两个方向均启用 |
| DMA 长度寄存器有效位宽 | 23 bit，单次长度最大 `2**23 - 1` 字节 |
| DMA DDR 地址映射 | `[0x00000000, 0x40000000)`，1 GiB |
| 时钟 | NPU、DMA、互连统一约 142.857132 MHz |

Python 的 `nbytes` 单位始终是**字节**。64 bit 流接口不意味着一次只能发送 8 字节；DMA 会把整个缓冲区转换成连续多拍。

控制基地址应从当前 `.hwh` / Overlay 元数据读取，例如 `overlay.ip_dict`、`overlay.axi_dma_0.mmio`、`overlay.npu_0.mmio`，不要猜测或复制别的工程的地址。

## 4. 最短可运行路线：直接调用现有驱动

在 AX7020 上使用配套部署包，其中 `lab8_driver.py`、`ax7020_runtime.py`、同名配对的 `lab8.bit` / `lab8.hwh` 和测试数据位于同一目录。在该目录运行：

```python
import numpy as np
from lab8_driver import Lab8NPU

# 这是 Lab8 的真实输入格式：每样本 512 个 INT8。
x = np.fromfile("inputs.bin", dtype=np.int8).reshape(-1, 512)[0]

with Lab8NPU("lab8.bit", timeout=2.0) as npu:
    result = npu.infer(x)
    print(result)
```

这段代码会加载 PL 位流；先确认正在使用的确实是要部署的版本。不要仅复制 `.bit` 而遗漏对应 `.hwh`。

如果使用 **PS API v2 的匹配硬件和驱动**，可以批量调用：

```python
xs = np.fromfile("inputs.bin", dtype=np.int8).reshape(-1, 512)
with Lab8NPU("lab8.bit", timeout=2.0) as npu:
    npu.prepare_batch(len(xs))  # 提前分配，避免把分配计入稳定态推理耗时
    result = npu.infer_batch(xs)
    print(result["predictions"])
```

## 5. 驱动底层怎样把数据送到 PL

关键步骤如下。下面是流程摘录，完整的超时、错误恢复和释放逻辑以现有 `Lab8NPU` 为准。

```python
from pynq import Overlay, allocate
import numpy as np

overlay = Overlay("lab8.bit")
dma = overlay.axi_dma_0
regs = overlay.npu_0.mmio

# 普通 np.zeros 不能替代 DMA 缓冲区。
tx = allocate(shape=(520,), dtype=np.uint8)
rx = allocate(shape=(168,), dtype=np.uint8)

# 本工程的初始化：清 NPU 状态。它不是通用 HLS ap_start。
assert regs.read(0x00) == 0x4C414238
regs.write(0x04, 1)

# 8 字节小端命令头 + 512 字节 INT8 数据。
tx[:8] = np.frombuffer((1).to_bytes(8, "little"), dtype=np.uint8)
tx[8:] = x.astype(np.int8, copy=False).view(np.uint8)
rx.fill(0)

# 先挂接收，再启动发送，避免结果返回时没有接收通道。
dma.recvchannel.transfer(rx, nbytes=8)
dma.sendchannel.transfer(tx, nbytes=520)

# 此后必须执行有超时的完成检查、接收缓存失效、实际长度校验。
# 调用现有驱动的 _wait_dma() / _exchange() 实现这些步骤。
# 不能在这两次 transfer 后立即读取 rx，transfer 是启动而不是完成。
```

缓冲区要求：

1. 用 `pynq.allocate()` 获取设备可访问的缓冲区；普通 NumPy 数组只有 CPU 视角，不能直接当 DMA 物理内存使用。
2. 检查 `buffer.physical_address` 与 `buffer.nbytes`，整个范围须落在 DMA 的实际地址映射内。本工程上界是 `0x40000000`，不是任意 Zynq 都如此。
3. PS 写完后、DMA 读取前要保证缓存已刷出；DMA 写完后、PS 读取前要保证缓存已失效。本项目使用 PYNQ 的 `transfer()` 与完成处理完成这些操作。
4. v2 的 `_wait_dma()` 是针对已核查的 PYNQ 3.0.1 simple DMA 行为做的优化，包含 `recv._active_buffer.invalidate()`，依赖私有属性。换 PYNQ 版本或 DMA 模式时应重新核查，不能只复制轮询部分。
5. DMA 仍在运行时不能释放或重用正在传输的缓冲区。异常时先停止/复位 DMA 和应用状态；确认 DMA 不再访问后再释放。
6. 复用已分配的缓冲区；不要在每个 token 的热路径反复分配物理连续内存。

## 6. 当前 Lab8 的包格式：用它理解方法，不要当作大模型协议

### CMD1：单样本推理

| 请求字节偏移 | 内容 |
|---|---|
| 0～7 | 64 bit 小端整数 `1`，字节为 `01 00 00 00 00 00 00 00` |
| 8～519 | 512 个有符号 INT8 输入，保持原始二进制位模式 |

发送 520 字节，64 bit 流上共 65 拍，每拍 `TKEEP=0xFF`，仅最后一拍 `TLAST=1`。

PL 返回 **1 个有效字节**，分类值为 0 或 1；末拍 `TKEEP=0x01`、`TLAST=1`。驱动设置 8 字节接收容量，并要求实际接收长度为 1。

`rx` 分配容量、`recv.transfer(..., nbytes=...)` 的容量、PL 实际有效字节数是不同概念：这里分别是 168、8、1。

INT8 的 `-1` 在线上传输是 `0xFF`，不是字符串 `"-1"`，也不是把负数截断成零。使用 `.view(np.uint8)` 保留比特；接收有符号结果时再 `.view(np.int8)`。

### CMD2：读取上一轮的逐层输出

只发送 8 字节小端命令 `2`。应先成功完成推理，再读对应结果。

返回 162 个 INT8：FC1 128 个、FC2 32 个、FC3 2 个。驱动接收容量 168 字节，要求实际长度 162 字节。末拍只有 2 个有效字节，对应 `TKEEP=0x03`。

### CMD3：批量推理，仅匹配的批量版本支持

头为 64 bit 小端整数 `(N << 32) | 3`；随后连续放 N 份 512 字节样本。整个请求总长 `8 + N*512`，请求最后一拍才置 `TLAST`。

返回 `N*8` 字节，每样本 8 字节：分类 1 字节、两个 INT8 分数各 1 字节、5 字节零填充。驱动允许 `1 <= N <= 16383`，同时受 DMA 最大长度和可用连续内存约束。

“512 维输入”与“192/256/512 路计算阵列”是两个概念，不能因阵列路数变化就更改输入长度。

## 7. PL 侧必须实现的流握手

- 只有 `TVALID && TREADY` 同时为 1，才真正传输一拍。接收计数器、写 RAM 地址和计算状态只能在握手成功时推进。
- 发送方在 `TVALID=1 && TREADY=0` 时必须保持 `TDATA/TKEEP/TLAST` 稳定。
- `TKEEP[i]` 表示 `TDATA[8*i +: 8]` 这个字节是否有效。
- `TLAST` 表示当前 DMA 包的结束。本工程 PL 输出必须正确产生它，否则接收可能一直等待或报错。
- 输入 `TLAST` 由 MM2S 根据本次发送长度产生；在 PS 拆成多次 DMA 发送时，每次都会形成独立包。不能假定多个 transfer 会自动拼成一个无边界的大包。
- 一个包内有多个样本或 token 时，是否每个样本结束就输出 `TLAST`，必须由双方协议规定；不能凭计算单元的“完成”脉冲直接生成。
- 本 Lab8 包装层检查输入 `TKEEP` 和 `TLAST` 是否符合预期；包长度错不只是“少算一点”，可能进入排空/错误响应状态。

## 8. 调试时读哪些状态

以下 NPU 地址全部是相对于 `overlay.npu_0.mmio` 的偏移。

| 偏移 | 含义 |
|---|---|
| `0x00` | 签名 `0x4C414238` |
| `0x04` | 写 bit0 触发软件复位；写 bit1 清统计 |
| `0x08` | 包状态、核心状态、特征有效、busy 等，位定义见 RTL |
| `0x0C` | 名义时钟 Hz，当前 `142857132` |
| `0x10` | 完成任务数 |
| `0x14` | 错误计数 |
| `0x18` | 最近核心计算周期 |
| `0x1C` | 最近 PL 事务周期 |
| `0x20` | 最近请求有效字节数 |
| `0x24` | 最近响应有效字节数 |
| `0x28` | 最近错误码 |
| `0x2C` | 最近命令 |
| `0x30` | 自由运行 tick |

DMA 的 MMIO 与 NPU 的 MMIO 是两个不同寄存器空间，不要混用偏移：

- `dma.mmio.read(0x04)`：MM2S 状态。
- `dma.mmio.read(0x34)`：S2MM 状态。
- 对本工程的 simple DMA，状态 bit0 是 Halted，bit1 是 Idle，`0x70` 掩码覆盖三个 DMA 错误位。先检查错误，再判断两通道是否完成。
- 完成处理后检查 `dma.recvchannel.transferred`，不能把“分配了多少空间”当成“实际收到了多少字节”。

建议排查顺序：

1. 核实 bit/hwh、IP 名称和协议版本，读取 NPU 签名。
2. 核实 DMA 缓冲区物理地址及完整可达范围、传输字节数。
3. 核实先启动接收、再启动发送，并设置有界超时。
4. 超时时保留两个 DMA 状态、NPU 状态、字节计数和错误码，再恢复；不要先复位把证据清掉。
5. MM2S 不结束时，重点查 PL 输入 `TREADY`、复位和时钟；S2MM 不结束时，重点查 PL 是否输出、`TLAST`、接收容量及背压。它们是排查线索，不是唯一成因。
6. 有数据但数值不对时，检查缓存、字节序、有符号解释、打包布局和量化参数。
7. 必要时用 ILA 同时观察双向流的 `TVALID/TREADY/TDATA/TKEEP/TLAST`。

现有 `reset_dma()` 会复位 NPU 与整个 DMA，再有界等待复位/启动完成。不要只清软件变量就继续发下一个请求。

## 9. 迁移到“大模型部署”时应怎样改

先核实目标板、操作系统、驱动栈、DMA 模式与 PL 接口。上述 Python 示例依赖 PYNQ；若新环境是裸机或其他 Linux 驱动，保留同一数据通路概念，改用对应的缓冲区分配、DMA 地址映射、缓存维护及完成接口。

第一步先跑通一个很小的回环/固定响应包，逐字节比较。然后再加权重装载和计算，避免同时调协议与模型。

新模型至少需要明确：

| 必须约定的内容 | 要回答的问题 |
|---|---|
| 操作类型 | 加载权重、输入激活、计算、读回分别是什么命令？ |
| 数据布局 | INT4/INT8/FP16？维度顺序、字节序、INT4 高低半字节顺序？ |
| 量化参数 | scale / zero point / 分组参数由谁传、存在哪里？ |
| 目标位置 | layer / tensor ID、PL 存储区、分块 offset 如何表示？ |
| 长度和分块 | 每块有效字节数、总长度、块序号和最后一块如何表示？ |
| 完成与错误 | 哪个响应表示权重已存好、哪一个表示计算完成？失败怎样恢复？ |
| 存储能力 | 权重、激活、KV cache 分别在 PS DDR、PL BRAM 还是其他存储？ |
| 吞吐 | 允许多大在途数据、何时允许覆盖或复用缓冲区？ |

可采用“带版本的命令头 + payload + 明确响应”的新协议，但必须同时修改 PS 打包和 PL 解析。当前 RTL **不会自动识别**大模型权重文件、任意 tensor 或新增命令。

MM2S 只负责把 DDR 中的字节送到 PL 流口。数据收到后写进哪块 BRAM、如何定位权重、何时可供计算使用，都是 PL 端需要实现的功能。

如果新加速器自行作为 AXI master 读取 DDR，则走的是另一种架构，需要配置它的地址寄存器、突发访问和完成机制；不要强行套用这里的 AXI-Stream 命令格式。

大于单次 DMA 长度或可分配缓冲区的数据要分块。每块都是独立 DMA 包，PL 应支持跨包组装；禁止假定一个大模型可以整体塞进片上存储。

性能报告分别记录：数据准备/打包、DMA 窗口、PL 计算、PS 总 API 时间。DMA 等待时间不等于纯链路传输时间，当前 `ps_end_to_end_us` 历史字段实际指主机 DMA 调用窗口。不要直接拿它减 PL 计时得到“软件开销”。

## 10. 给接手 AI 的执行要求

请先阅读本文件列出的真实源码，确认目标工程后独立派生实验，保留默认工程及历史基线。按“最小数据包 → 结果回读 → 分块权重 → 小规模计算 → 完整模型”的顺序推进。

有源码但没有跑板时，请明确写“尚未板测”；仿真、综合、布局布线与真正板上数据传输是不同验证层级。现有 Lab8 的板测证据不能代替新大模型工程的验证。
