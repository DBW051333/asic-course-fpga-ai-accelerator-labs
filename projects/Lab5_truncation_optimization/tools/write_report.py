#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
from collect_results import collect
from search_quantization import ROOT,BASE

def main():
    rows=collect();routed=[r for r in rows if r.get('physical_pass') and r['sim_status']=='passed']
    keep=[r for r in routed if r['correct']>=37 and r['ties']==0 and r['disagreements']==0]
    best=min(keep,key=lambda r:r['latency_ns']) if keep else None
    precise=[r for r in keep if not r.get('product_cut')]
    layer_best=min(precise,key=lambda r:r['latency_ns']) if precise else None
    completed=sum(r['impl_status']=='passed' for r in rows)
    text=['# Lab5 截位优化试验记录','',
    '日期：2026-10-05。原推荐版本保存在原目录。本轮使用独立目录，保留每个候选的 RTL、配置、整数参考、仿真、综合、布线及失败记录。','',
    '## 1. 基线和比较口径','',
    f'基线：`{BASE.name}`。三层网络 512→128→32→2，168 拍延迟、129 拍启动间隔，原最终布线通过周期 5.26 ns。单次计算 883.68 ns，启动间隔 678.54 ns。资源 23,944 LUT、41,984 FF、61 BRAM Tile、216 DSP。','',
    '基线和所有功能候选均检查同样的 48 次连续重叠请求：课程的 42 个样本，加原 Lab5 的课程输入、全 −128、全 127、正负交替、固定种子随机、FC1 极值输入。每个版本逐项检查三层 7,776 个值和地址，验证重叠请求的独立性。分类统计仅使用课程 42 个带标签样本。','',
    '使用已有 Lab6 和配套 int8_results.txt 的标签规则：score0 < score1 时预测标签 1，否则为 0，相等归 0。PPT 第 6 页的标签方向与配套数据文件相反；此处保持数据文件和已有工程的规则。未截位基线 37/42（88.10%），错误样本索引为 21、23、25、40、41，索引从 0 开始。','',
    '## 2. 课件依据和截位方法','',
    '依据 Lab6 第 8～11 页：先完成乘加、偏置和激活，再做层输出截位。42 个原始样本的 FC1/FC2/FC3 最大绝对值为 80,805 / 39,386,422 / 17,379,948,761，与课件一致。后续层的移位根据前层已截位的实际范围重新计算。第 17 页要求三层全截位，并至少比较有符号 4 位和 8 位。','',
    '必选 8 位方案使用右移 10 / 9 / 8 位；必选 4 位方案使用 14 / 8 / 9 位，与已有 Lab6 完整整数模型一致。FC2 的 9 位移位基于实际截位后输出范围，未照搬课件举例的 8 位。权重及偏置仍为原模型有符号 INT8，偏置的缩放约定沿用 Lab6。','',
    '层间位宽同步缩窄 FC2/FC3 输入、乘积、完整累加器、快照和输出选择总线。FC1 保留 23 位完整累加。FC2 累加宽度为 FC1 输出位宽+15，FC3 为 FC2 输出位宽+13，均覆盖全部对应输入乘加范围。所有层输出量化一次。','',
    'floor_wrap：算术右移后选取指定低位，与课件的位选择一致。floor_sat：向下取整并饱和。round_sat：加半个量化步长后算术右移并饱和，恰好半步时向正无穷取整。舍入饱和逻辑均为固定参数，未使用运行时桶形移位器。','',
    '额外策略为 FC1 每个 16 位乘积先舍入并丢弃 K 个低位，再送入较窄的加法树，最后恢复 2^K 倍尺度。此策略会改变层数值，是独立的近似试验，不属于原 Lab6 的纯层输出截位。单个乘积误差≤2^(K−1)，512 项 FC1 的最坏绝对误差界为 512×2^(K−1)，该界不保证分类不变。','',
    '其中 prereg 方案把乘积舍入放入原乘积输出寄存器之前，减少加法树输入端组合逻辑与寄存器有效位。流水线级数及 168 拍延迟不变。','',
    '另有 tree8 方案将 FC1 的两级组合加法拆开，让 8 级加法各自寄存。该版本保留完整乘积，只做 Lab6 的层输出截位，数值与标准 8 位方案相同；延迟由 168 增加为 169 拍，启动间隔仍为 129 拍。最终按照周期数乘通过周期比较单次时间。','',
    'K=1～8 的加法树与 FC1 累加位宽还按固定权重、每个输入可取全部 INT8 范围做区间证明：各级节点不溢出，FC1 所有累加前缀均在 23 位范围内。证明见 results/product_width_proof.json。','',
    '## 3. DSP 分配和精确打包','',
    'standard 保留 FC2 的独立乘法。packed 利用后两层每对输出共享输入，将两个有符号权重组成 (w1<<16)+w0，一次乘法生成两个积，并对高半部做符号修正。该打包运算精确，不增加量化误差。4/6/8 位输入分别穷举 1,048,576 / 4,194,304 / 16,777,216 组 (x,w0,w1)，低积与修正高积均通过。证明记录见 results/packing_proof.txt。','',
    'DSP_LANES 指 FC1 中使用 DSP 的打包通道数，其余通道保留原分段逻辑乘法。packed 版本将 FC1 提高到 200 个 DSP，FC2 用 16 个，FC3 用 4 个，总计 220。4 位 LUT 版本将后两层乘法放在逻辑中，FC1 使用 220 个 DSP。DSP 实际总量取自综合/布线报告，不按位宽猜测。','',
    'rompack 进一步把固定权重打包提前到初始化数据生成，使 FC2/FC3 权重 RAM 直接输出有符号 25 位打包权重，消除 RAM 与乘法器之间的打包加法。原始权重不变，打包后的数据在各候选 data/fc*_packed_weights.mem 中。该优化在功能上与对应 packed 方案相同。','',
    '## 4. 功能和综合候选对比','',
    f'整数层输出截位搜索共 4,226 组，另检查 FC1 乘积截掉 1～8 位。已生成 {len(rows)} 个 RTL 候选，完成 {sum(r["sim_status"]=="passed" for r in rows)} 个候选的完整功能检查、{sum(r["synth_status"]=="passed" for r in rows)} 个综合、{completed} 个完整布线。','',
    '| 候选 | 层位宽 | 右移 | 策略 / FC1 低位 | 正确 /42 | 相等数 | 与基线分类不同 | 功能 | 综合 | 布线 |',
    '|---|---|---|---|---:|---:|---:|---|---|---|']
    for r in rows:
        cut=r.get('product_cut',0);strategy=r['mode']+(f' / K={cut} '+r.get('product_cut_stage','tree') if cut else '')
        if r.get('tree_stages')==8:strategy+=' / tree8'
        text.append(f'| [{r["name"]}]({ROOT}/{r["name"]}/config.json) | {"/".join(map(str,r["widths"]))} | {"/".join(map(str,r["shifts"]))} | {strategy} | {r["correct"]} | {r["ties"]} | {r["disagreements"]} | {r["sim_status"]} | {r["synth_status"]} | {r["impl_status"]} |')
    text+=['','not_run 表示该阶段未运行，不代表时序通过或失败。仅进行功能检查的低位数方案保留作误差对照，硬件优先实现能明显缩窄加法树的候选。未布线方案不参与速度排名。','',
           '## 5. 完成布线的性能比较','',
           '| 方案 | 拍数 | 通过周期 ns | 时延 ns | 启动间隔 ns | LUT | FF | BRAM | DSP | WNS ns | WHS ns | WPWS ns |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|',
           '| 原 Lab5 最佳 | 168 | 5.26 | 883.68 | 678.54 | 23944 | 41984 | 61 | 216 | 0.005 | 0.050 | 1.650 |']
    for r in sorted(routed,key=lambda r:r['latency_ns']):
        a=r['resources'];text.append(f'| {r["name"]} | {r["cycles"]} | {r["period"]:.2f} | {r["latency_ns"]:.2f} | {r["interval_ns"]:.2f} | {a["lut"]:.0f} | {a["ff"]:.0f} | {a["bram"]:g} | {a["dsp"]:.0f} | {r["wns"]:.3f} | {r["whs"]:.3f} | {r["wpws"]:.3f} |')
    text+=['',
           '综合和布线器件均为 xc7z020clg400-1。统一初始目标 4.8 ns，使用 Explore 布局、物理优化及布线。每个完成布线的设计按 0.01 ns 分辨率重新约束，保存通过周期的 timing_final.rpt、final_routed.dcp、final_clock.xdc，同时保留再缩短 0.01 ns 的 timing_boundary.rpt。只将 setup、hold、pulse width 均通过的结果列入此表；4.8 ns 的负 WNS 不算达到该频率。','',
           '## 6. 当前选择与精度结论','']
    if best:
        a=best['resources'];text+= [f'保持这 42 个样本分类与基线一致的最快完成方案：**{best["name"]}**。通过周期 {best["period"]:.2f} ns，延迟 {best["latency_ns"]:.2f} ns，比原最佳减少 {best["latency_reduction_percent"]:.2f}%，速度比 {best["speedup_vs_baseline"]:.3f}。准确率 {best["correct"]}/42，相等数 {best["ties"]}。','',
          f'相对原基线，LUT 变化 {(a["lut"]/23944-1)*100:+.2f}%，FF 变化 {(a["ff"]/41984-1)*100:+.2f}%，BRAM {a["bram"]:g}，DSP {a["dsp"]:.0f}。','']
        if best.get('product_cut'):
            text+=[f'该最快方案包含 FC1 乘积低位近似。相对相同层输出截位而未做乘积近似的方案，三层截位输出最大绝对差分别为 {best["layer_max_error_vs_layer_only"]}。其分类一致仅在当前 42 样本成立，三层数值并不与未截位 Lab5 相同。','']
        (ROOT/'results/recommended.json').write_text(json.dumps(best,indent=2))
    if layer_best:
        text+=[f'只做层输出截位、保持已有 Lab6 8 位整数结果的完成方案：**{layer_best["name"]}**，周期 {layer_best["period"]:.2f} ns，延迟 {layer_best["latency_ns"]:.2f} ns。若需要严格遵循课件“完整 MAC 后截位”的口径，可选择该版本。','']
        (ROOT/'results/recommended_layer_only.json').write_text(json.dumps(layer_best,indent=2))
    area_candidates=[r for r in keep if r['latency_ns']<=883.68]
    if area_candidates:
        area=min(area_candidates,key=lambda r:r['resources']['lut'])
        a=area['resources']
        text+=[f'在本轮完成且不慢于原基线的方案中，较省 LUT 的版本是 **{area["name"]}**：{a["lut"]:.0f} LUT、{a["ff"]:.0f} FF，周期 {area["period"]:.2f} ns、延迟 {area["latency_ns"]:.2f} ns。该版本包含乘积近似时应按配置中的 product_cut 判断，与 Lab6 标准层输出截位数值不同。','']
        (ROOT/'results/recommended_area.json').write_text(json.dumps(area,indent=2))
    if best and best.get('tree_stages')==8:
        balanced=next((r for r in precise if r['name']=='q8_lab6_rompack_d200'),None)
        if balanced:
            extra=best['resources']['ff']-balanced['resources']['ff'];gain=(balanced['latency_ns']-best['latency_ns'])/balanced['latency_ns']*100
            text+=[f'较均衡的纯层截位版本是 **{balanced["name"]}**：{balanced["latency_ns"]:.2f} ns，{balanced["resources"]["ff"]:.0f} FF。最快 tree8 版本仅比它减少 {gain:.3f}% 单次时间，却多用 {extra:.0f} FF。若更重视寄存器资源，可采用该 7 级版本。','']
            (ROOT/'results/recommended_balanced.json').write_text(json.dumps(balanced,indent=2))
    text+=['4 位原方案 36/42（85.71%），但 27 个样本分数相等，其中多数按默认标签 0 得分，因此分类信息损失明显。8 位原方案 37/42（88.10%），没有相等分数，分类与基线一致。部分舍入方案达到 38/42（90.48%）。这些移位和位宽由同一组 42 样本选择，38/42 属于这组数据的观察结果，尚不能据此判断未见数据准确率提高。','',
           'floor_wrap 的移位按课程输入范围校准，在课程 42 样本上无溢出，但极值输入会回绕。各 config.json 的 overflow_counts 记录 42 样本越界数，stress_overflow_counts 记录全部 48 请求。饱和版本避免回绕，但可能剪掉幅值。','',
           '不采用为最快方案的原因：单纯增加 DSP 并做动态权重打包，完成周期为 5.33 ns；加法树入口舍入版本为 6.67 ns，其关键路径转移到 FC2 权重 RAM、打包加法与 DSP 之间；寄存器前舍入但仍动态打包为 6.68 ns。提前打包到 ROM 后，这类路径改善到 5.22 ns，且只用 15,610 LUT，但仍慢于不做乘积近似的 5.08 ns。标准 4 位和 6 位舍入版本的通过周期分别为 5.30 / 6.94 ns，均未提供更快单次时间。','',
           '## 7. 复现与文件','',
           '输入与模型沿用原最佳版本的初始化 ROM。42 样本和六组扩展输入通过测试平台更换 ROM 内容进行功能验证；现有物理接口没有运行时加载输入端口。本轮物理资源和时序均使用与基线相同的课程样本 1 ROM 初始化。换物理 ROM 输入时需更新初始化文件并重新综合，资源和时序也可能随初始化数据改变。','',
           '构建脚本：tools/search_quantization.py、tools/build_candidates.py。搜索结果：results/quantization_search.csv / .json。逐候选数据：config.json、data/fc*_expected.mem、results/rtl_samples.csv。资源及时序对比：results/hardware_comparison.csv / .json。各阶段完整日志、耗时和状态：results/*_console.log、results/run_status.json。','',
           '运行指定候选：','',
           '```sh',
           f'cd {ROOT}',
           'python tools/run_trials.py sim <候选名>',
           'python tools/run_trials.py synth <候选名>',
           'python tools/run_trials.py impl <候选名>',
           'python tools/collect_results.py',
           'python tools/write_report.py',
           '```','',
           'Vivado 仿真/布线使用 general.maxThreads=8，后续综合使用 4，以控制综合子进程的内存占用；首两份综合日志实际使用 8。各阶段耗时是本机实际运行记录，部分阶段同时运行，且存在热状态与内存负载差异，不用这些耗时断言某线程设置必然更快。','',
           '时序结论适用于已约束内部时钟路径，外部 IO 延迟和板级引脚尚未定义，未做板上实测。保存的 DCP 是完成布线的设计，单次时间由已验证拍数与通过周期相乘。']
    verification=ROOT/'results/final_verification.json'
    if verification.exists():
        v=json.loads(verification.read_text())
        if best and v['selected']==best['name'] and v['status']=='passed':
            text+=['','## 8. 最终工程和复核','',
                 f'推荐版本的保存 DCP 已重新打开，复核 setup、hold、pulse width 通过，布线错误数为 0。导出工程按 {v["period"]:.2f} ns 设置时钟，并在这个参数下重新完成 48 次重叠请求、7,776 个值和地址检查，errors=0。记录见 results/final_verification_console.log、候选 results/timing_verified.rpt 和 results/route_status_verified.rpt。','',
                 f'[可直接打开的 Vivado 推荐工程]({v["project"]})','',
                 f'[推荐版本完成布线的 DCP]({ROOT}/{best["name"]}/results/final_routed.dcp)','',
                 '本轮 20 个 RTL 候选的功能检查、15 个候选综合和 9 个候选完整布线已全部按计划完成。最佳结果指本轮已完成的这些实施结果，不代表全局最优。']
    (ROOT/'Lab5截位优化对比报告.md').write_text('\n'.join(text)+'\n')
    (ROOT/'README.md').write_text(f'# Lab5 截位优化\n\n[完整比较报告]({ROOT}/Lab5截位优化对比报告.md)\n\n[逐候选数据]({ROOT}/results/hardware_comparison.csv)\n\n[推荐 Vivado 工程]({ROOT}/recommended/Lab5_truncation_recommended.xpr)\n\n'+
       (f'当前保持分类一致的最快完成方案：`{best["name"]}`，{best["latency_ns"]:.2f} ns。\n' if best else '试验进行中。\n'))
    source=json.loads((ROOT/'results/baseline_source_sha256.json').read_text())
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==v for p,v in source.items())
    print('Report written. Completed implementations:',completed)

if __name__=='__main__':main()
