from pathlib import Path
import json,subprocess
r=Path('/home/ding/vivado_project/Lab5_optimization')
subprocess.run(['python',str(r/'tools/collect_results.py')],stdout=subprocess.DEVNULL)
rows=json.loads((r/'results/all_results.json').read_text());eligible=[x for x in rows if x.get('final_wns',x['wns'])>=0 and x.get('final_whs',x['whs'])>=0 and x['cycles']]
best=min(eligible,key=lambda x:x.get('final_latency_ns',x['latency_ns']));name=best['name'];period=best.get('final_period',best['period']);ns=best.get('final_latency_ns',best['latency_ns'])
lines=['| 方案 | 周期 | 布线目标 ns | 目标 WNS ns | 复核通过周期 ns | 通过时延 μs | LUT | FF | BRAM | DSP |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in rows:
 fp=x.get('final_period',x['period'] if x['wns']>=0 else None);lat=x['cycles']*fp/1000 if fp and x['cycles'] else None
 lines.append(f"| {x['name']} | {x['cycles']} | {x['period']:g} | {x['wns']:+.3f} | {fp:g} | {lat:.4f} | {int(x['lut'])} | {int(x['ff'])} | {x['bram']:g} | {int(x['dsp'])} |" if fp and lat else f"| {x['name']} | {x['cycles']} | {x['period']:g} | {x['wns']:+.3f} | 未通过 | — | {int(x['lut'])} | {int(x['ff'])} | {x['bram']:g} | {int(x['dsp'])} |")
explore_lines=[]
for d in r.glob('stream*'):
 f=d/'results/final_clock_explore.json'
 if f.exists():
  x=json.loads(f.read_text());old=d/'results/final_clock_default.json';oldx=json.loads(old.read_text()) if old.exists() else json.loads((d/'results/final_clock.json').read_text());explore_lines.append(f"- {d.name}：默认实现 {oldx['period']:g} ns；Performance_Explore {x['period']:g} ns，WNS {x['wns']:+.3f} ns、WHS {x['whs']:+.3f} ns。")
explore_text='\n'.join(explore_lines)
s=f'''# Lab5 三层网络优化报告

日期：2026-10-05。器件：xc7z020clg400-1；工具：Vivado 2025.2。

## 当前推荐结果

推荐工程：[{name}]({r/name}/vivado/{next((r/name/'vivado').glob('*.xpr')).name})。

一次完整 512→128→32→2 网络需要 **{best['cycles']} 个周期**。布线后内部时钟 **{period:g} ns** 复核通过，对应 **{ns/1000:.4f} μs**。相对原始 1834 周期、100 MHz 的 18.34 μs，完成时间缩短 **{(1-ns/18340)*100:.2f}%**，约 **{18340/ns:.2f} 倍**。不同频率的比较以周期数乘时钟周期计算。

资源：{int(best['lut'])} LUT、{int(best['ff'])} FF、{best['bram']:g} BRAM Tile、{int(best['dsp'])} DSP；器件限制为 53200 LUT、106400 FF、140 BRAM Tile、220 DSP。

## 1. 重新核准原始版本

原始版本分别实例化三层 FC，通过打包器和中间 RAM 串行交接。FC2 采用 issue/wait/accumulate 多拍处理，FC3 为两个输出重复调用 32 路宽乘法。

- 原始综合报告：10345 LUT、17112 FF、77 BRAM Tile、288 DSP。DSP 超过器件的 220 个，无法完整实现。
- 原始正确计时：1834 周期，100 MHz 下 18.34 μs；连续三次请求全部 486 个值和地址一致。
- 最初测试平台使用 `!=`，未知值可能漏报；已改为 `!==`。早期 64×16 方案还修正了 FC3 地址宽度和输入写地址，真实计算正确但约 3646 周期，速度劣于原始，不采用。
- 原始资源采用综合报告；以下新方案资源采用完整网络物理封装的布线报告，口径差异明确保留。

## 2. 借鉴 Lab4 的内容

参考：[Lab4资源演进与代表版本](/home/ding/vivado_project/Lab4_optimized/adder_experiments/Lab4资源演进与代表版本.md)。

1. 使用单累加器替代多组累加暂存，先降低无效 LUT/FF。
2. 权重按实际读取顺序重排，取消大字宽切片选择和不必要中间 RAM。
3. 比较 64、128 路及不同加法树流水分配；先检查功能，再读取真实布线路径。
4. 后级加法位宽增大，优先拆开较宽的连续加法，不能只追求相同逻辑层数。
5. 比较实际完成时间，而不是仅凭频率或周期数判断优劣。

## 3. Lab5 的结构创新

### 跨层流式计算

FC1 每产生一个输出，FC2 的 32 个独立 MAC 就处理该输入；FC2 输出再直接送入 FC3。三层都有独立运算单元，没有复用同一个 FC 模块。中间完整输入 RAM 与 packer 被移除。

FC3 只有两个输出，因此先从 32 路乘法归约改为两条持续累加链。后续扩展为每拍处理 2、4、8 个 FC2 输入，分别减少尾部输出串行等待。

### 有证明的精确位宽

对固定实验权重和任意 signed 8-bit 输入作区间界计算，覆盖每个神经元与累加前缀：

| 数据 | 界限 | 内部有符号宽度 |
|---|---:|---:|
| FC1 ReLU 前与所有累加前缀 | −3575930…3574270 | 23 |
| FC2 ReLU 前 | −14827213425…14809348815 | 35 |
| FC3 累加结果 | −16027169531066…9805364218938 | 45 |

外部仍输出 32/48/64 位，通过符号扩展恢复接口宽度。这里没有量化、近似或有效位丢失；权重改变后必须重新计算界限。完整字宽对照工程 `stream128_full` 也已通过，使用 198 DSP。

八路尾部的局部求和最多八个非负 35 位输入乘以 signed 8-bit 权重，仍能由 45 位精确表示；完整局部树先保留 46 位，再使用已证明冗余的符号位收窄。

### 一个 DSP 计算两个 FC1 输出的乘积

同一输入 x 对应两个权重 w0、w1，构造 `A=(w1<<16)+w0`，用一个 25×8 DSP 计算 P=A×x：

- p0 = signed(P[15:0])。
- p1 = (P>>>16) + (p0<0)。

符号修正使两个乘积均精确。全部 **16777216** 组 x/w0/w1 组合已穷举通过，见 [DSP 打包证明]({r}/results/dsp_packing_proof.txt)。128 条打包乘法链一次处理两个神经元，FC1 计算组数减半。

### DSP 与逻辑乘法混合

扩展到 256 路后，每个神经元只需两组。FC1 的部分通道采用打包 DSP，剩余通道用逻辑实现两个 8×8 乘法，使三层整体保持在 220 DSP 内。单纯逻辑 8×8 乘法成为高频瓶颈，于是拆成四个 4×4 部分积，寄存交叉项和合并结果，并同步延迟 DSP 通道。

对于 `a=al+16×ah`、`b=bl+16×bh`，低半字无符号、高半字有符号：

`a×b=al×bl+16×(ah×bl+al×bh)+256×ah×bh`。

全部 **65536** 组 signed 8×8 输入穷举通过，见 [部分积证明]({r}/results/nibble_decomposition_proof.txt)。

### 流水线与尾部并行

- 4 级树的最后宽加法、逻辑乘法均出现过负时序余量。
- 5 级 2/2/2/1/1 树与部分积流水线组合，改善逻辑乘法后，关键路径转移到中间两层连续加法。
- 7 级 2/1/1/1/1/1/1 树进一步拆开这些宽加法，增加两拍并比较实际频率收益。
- FC2 输出每拍 2/4/8 个，FC3 同拍计算对应输入，功能周期分别为 173/166/163；四路配七级树为 168 周期。

### 连续请求的重叠执行

增加 FC2 结果快照，使输出读取与下一次输入累加并行；FC1 在发完全部乘法任务后给出 `ready_o`。FC1 全部累加前缀也经权重区间证明可用 23 位，进一步缩短累加器进位链；64×16-bit 小偏置 ROM 强制使用分布式存储，避免 BRAM 读取叠加宽加法路径。六组不同输入连续重叠计算，972 个值及地址全部一致，启动间隔为 **129 周期**，每次计算延迟仍为 **168 周期**。`done_o` 表示一次结果完成，`ready_o` 表示可以发起下一次请求，分别使用。

吞吐功能对照版见 `stream_pair256_burst_tree7_clk4p8`，合并 23 位累加与小 ROM 改进的候选为 `stream_pair256_burst_exact23_tree7_clk4p8`，日志 `results/burst_console.log`。初始化 ROM 的输入更新方式仍与单次候选一致。

### 权重 RAM 分块与地址流水

七级加法树完成布线后，瓶颈转移至共同地址寄存器驱动大字宽 RAM。`stream_pair256_banked_exact23_tree7_clk4p8` 将权重拆为八块，每块独立地址寄存器与局部同步读取，输入同步延迟一拍；完整网络 169 周期，重叠启动间隔仍为 129 周期。分块文件内容与原权重完全一致。

## 4. 实验数据

{chr(10).join(lines)}

“布线目标”是实施布局布线时使用的约束。复核时在同一份完成布线的设计上重新约束时钟，重新计算 setup、hold、pulse width，保存独立的 `final_routed.dcp` 和 `timing_final.rpt`；这不是只用 WNS 推算频率。`timing_boundary.rpt` 是再缩短 0.01 ns 的边界复核，保留边界失败报告，并以 0.01 ns 分辨率选择最短通过周期。负 WNS 的目标不计为达成。

早期四级 3/2/2/1 与未拆乘法的五级树均通过三次功能检查，保留在 `stream_pair256_3221_clk5`、`stream_pair256_five_clk5`；没有完整布线数据，不计入最快方案。已终止后续明显更紧的重复失败时钟试验。

### 最后一轮比较与收敛

{explore_text}

八路尾部虽减少周期，实际比四路慢；八块权重 RAM 的独立地址方案也变慢，未采用。单块 RAM 的局部输入寄存器方案通过周期为 5.44 ns，比 23 位累加与快照版本的 5.31 ns 慢，未采用。最终 Performance_Explore 由 5.31 ns 改善至 5.26 ns，仅约 0.94%，本轮停止追加试验。

220 DSP 全利用派生试验已取消排队布线，不计入推荐结果；没有把未完成的方案视为时序通过。

## 5. 功能证据

所有进入布局布线比较的方案至少连续三次请求，严格核对三层全部 486 个值及地址。最终候选额外覆盖六组连续请求、972 个值及地址：课程输入、全 −128、全 127、正负交替、固定种子随机输入、使 FC1 某神经元达到 3574270 上界的输入。CPU 整数模型逐层生成黄金值，课程输入还与给定参考文件逐项核对。

课程最终结果为 `1444462170`、`−1667237270`。向量与黄金值见 [验证清单]({r}/data/validation/manifest.json)，每个候选的日志保存在 `results/validation_console.log`。

输入沿用实验的初始化 ROM 方式。六组行为仿真通过更新输入 ROM 验证算法；综合工程默认使用课程输入，改变初始化输入后需要重新生成对应存储文件并综合。

## 6. 复现与工程使用

推荐目录：`{r/name}`。

- 行为仿真：在工程目录执行 `vivado -mode batch -source tools/create_sim.tcl`。
- 串行综合与布线：执行 `vivado -mode batch -source tools/run_serial_impl.tcl`（若无该脚本则用 `run_impl.tcl`）。
- 默认布线完成后复核时钟：执行 `vivado -mode batch -source tools/finalize_clock.tcl`。
- 最终选用 Performance_Explore 的工程：执行 `vivado -mode batch -source tools/run_explore.tcl` 重现优化布局，并使用 `tools/verify_final.tcl` 复核已保存的最终 DCP。
- 六组验证：执行 `vivado -mode batch -source tools/run_final_validation.tcl`。
- 打开最终物理结果：在 Vivado 中打开 `results/final_routed.dcp`，时钟约束见 `results/final_clock.xdc`。

仿真顶层为 `lab5_top`，物理顶层为 `lab5_impl_top`。物理封装只对外暴露最终结果，三层完整运算仍全部保留；避免将所有中间调试总线当物理 IO 导致超出器件引脚数。多路尾部方案的 FC2 调试接口每拍同时提供多个相邻结果，地址表示该拍首个结果。

公共系数与输入初始化文件位于 `{r}/data`；现有绝对路径已配置。原始 Lab5 工程保留，候选工程与失败报告保留用于比较。

时钟结论适用于已约束的内部路径，外部 IO 延迟与板级引脚尚未定义。完成时间为功能周期与通过时序的内部周期换算，尚无板上实测结果。

## 7. 收敛依据

目前从中间 RAM/FSM、位宽、DSP 利用率、FC1 并行度、乘法分解、加法树分配、尾部并行度逐项推进。继续增加尾部并行度的周期收益从 15 拍、7 拍降至 3 拍；每次又必须把更多 FC1 DSP 换成逻辑乘法，增加面积与布线压力。最终选择以完整布线复核后的实际时间为准。

这表示本轮已尝试结构下的收益收敛；不能据此宣称所有可能架构的全局最优。进一步系统化的设计空间搜索或外部输入接口改造属于后续独立工作。
'''
(r/'Lab5三层网络优化报告.md').write_text(s)
(r/'results/recommended.json').write_text(json.dumps(best,indent=2))
print(name,period,ns)
