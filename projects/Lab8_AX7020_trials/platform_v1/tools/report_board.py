"""Produce a concise report from completed target implementation and board evidence."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
a=json.loads((R/'results/board/board_acceptance/acceptance.json').read_text());assert a['pass']
s=json.loads((R/'results/board/board_scalar/summary.json').read_text());assert s['correct']==42 and s['feature_values_checked']==6804 and s['feature_mismatches']==0
b=json.loads((R/'results/board/api_board_results.json').read_text());assert len(b['measurements'])==14
package=R/'evidence/benchmark_input_package.tar.gz'
assert hashlib.sha256(package.read_bytes()).hexdigest() in b['hashes'].values()
for name in ['lab8.bit','lab8.hwh','lab8_driver.py']:
 path=R/('overlay' if name.endswith(('.bit','.hwh')) else 'ps')/name
 assert hashlib.sha256(path.read_bytes()).hexdigest()==next(v for k,v in b['hashes'].items() if Path(k).name==name),name
summary=json.loads((R/'results/summary.json').read_text());t=summary['timing'];res=summary['resources']
lines=['# Lab8 AX7020移植与板测结果','', '2026-10-11。来源 `Lab8_integrated_192`，源基线 `lab8_128_resource_v1`。独立工程 `/home/ding/vivado_project/Lab8_AX7020_trials/platform_v1`。原综合版、指定双基线、smoke及默认入口保留。','', '## 硬件适配与实现','', '目标 xc7z020clg400-2；采用已通过smoke的AC7020社区PS预设，33.333333 MHz参考、32位1 GiB DDR、UART1。两路DMA解码0–0x3FFFFFFF。NPU/DMA/AXI共享FCLK0，目标7 ns。', '', f'重新量化模型逐文件一致，功能RTL仅调整路径，FC1仍为192路。LUT {res["lut"]:g}、FF {res["ff"]:g}、Slice {res["slice"]:g}、BRAM36等效 {res["bram36_equivalent"]:g}、DSP {res["dsp"]:g}。重开最终DCP：WNS {t["wns_ns"]:+.3f} ns、WHS {t["whs_ns"]:+.3f} ns，单时钟、完整布线、PL DRC无Error/Critical Warning，DSP乘法分配192/16/4。无未约束内部端点。','', '目标RTL48任务/7776逐层值、94批量样本/15228值通过；实际AMD DMA IP仿真42样本/6804值及异常恢复通过；目标与父工程成对批量仿真均7423周期。此项是仿真结果。8项主机驱动测试通过，包含初始DMA状态回归。','', '## 真实板测','',f'PYNQ {a["pynq"]}、Python {a["python"]}。Overlay加载、签名、首样本、42样本分类42/42及6804逐层值全通过，完成任务42、错误0。N=1/3/8/16/42/48/128各连续3批验证类别、signed scores和末样本特征。截断CMD1返回0xE3，正常包恢复、DMA复位恢复、Overlay重载后直接批量均通过。N>42重复课程样本，不是新增准确率数据。','',f'FCLK0寄存器0x100700、IO PLL反馈30、分频7×1，按板卡参考计算 {a["clock"]["register_derived_hz"]/1e6:.6f} MHz。三个NPU tick估计窗口与此一致；PYNQ默认50 MHz参考读数214.285714 MHz仅作为原始记录。频率是寄存器推算和tick辅助核查，未用仪器测量。','', '实际DMA使用0x380xxxxx高地址缓冲区，完整缓冲区均位于两路1 GiB解码内。核心216周期约1.512 μs；板上42批量事务7337周期约51.359 μs，区别于7423周期仿真窗口。', '', '## 实际API耗时','', '每组预热10次、测量100次，所有返回类别/分数逐次核对，组后核对特征。完整调用包含数据检查、打包、接收清零、DMA和统计；缓冲区提前分配，分配耗时另记，Overlay冷启动另记。主机DMA调用窗口与PL事务边界不同，不能相减归因。','', '| 模式 | N | API中位数 μs | API P95 μs | API吞吐中位数 样本/s | 主机DMA窗口中位数 μs |','|---|---:|---:|---:|---:|---:|']
for v in b['measurements']:
 st=v['stats'];lines.append(f'| {v["mode"]} | {v["N"]} | {st["api_wall_us"]["median"]:.3f} | {st["api_wall_us"]["p95"]:.3f} | {st["api_samples_per_second"]["median"]:.1f} | {st["host_dma_window_us"]["median"]:.3f} |')
lines+=['',f'冷启动Overlay/驱动耗时 {b["cold_overlay_driver_us"]:.3f} μs（含约0.7秒时钟tick核查，不能视为纯硬件下载耗时）。原始100次数据保存于 `results/board/api_board_results.json`。基准测试输入归档单独保留为 `evidence/benchmark_input_package.tar.gz`，其SHA256与基准报告对应；最终交付归档增加板测证据，包哈希因此不同，bit/hwh/驱动身份仍逐项匹配。','', '## 部署修复与验证范围','', 'PYNQ 3.0.1遇到同名XSA旁文件会错误解析bit；部署中XSA改名为lab8_ax7020_192.xsa，bit/hwh保持同名。三者来自同一新构建。驱动按PYNQ首次传输状态允许新启动的DMA分配批量缓冲区，同时拒绝活动DMA时扩容。运行时新增只读PLL/FCLK/tick核查和高DDR地址检查。','', '社区PS预设保留smoke同样的负DQS skew警告；现有启动系统/FSBL/DDR初始化文件未更换。当前板测验证该启动系统下的DMA和Lab8工作，不代表新XSA的PS初始化或全DDR压力测试通过。未实测功耗，未执行完整16383样本批量。','', '部署包 `deploy/lab8_ax7020_192.tar.gz`，板上目录 `/home/xilinx/jupyter_notebooks/Lab8_AX7020_192`。打开 `Lab8_AX7020_192.ipynb` 按顺序复跑。`SHA256SUMS`校验配套文件，migration.json记录身份，implementation_summary.json记录实现及板测摘要。','']
(R/'results/board_report.md').write_text('\n'.join(lines))
print('Verified benchmark identity and wrote board_report.md')
