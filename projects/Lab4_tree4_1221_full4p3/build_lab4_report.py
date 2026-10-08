from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUT = "/home/ding/vivado_project/Lab4/output/docx/Lab4代码与仿真操作说明.docx"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_margins(cell, top=80, start=100, bottom=80, end=100):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_run_font(run, size=11, bold=False, color="000000"):
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def add_text(doc, text, bold_lead=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(7)
    p.paragraph_format.line_spacing = 1.35
    if bold_lead and text.startswith(bold_lead):
        set_run_font(p.add_run(bold_lead), bold=True)
        set_run_font(p.add_run(text[len(bold_lead):]))
    else:
        set_run_font(p.add_run(text))
    return p


def add_code(doc, lines):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_shading(cell, "F3F5F7")
    set_cell_margins(cell, 100, 130, 100, 130)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(lines)
    r.font.name = "Liberation Mono"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    r.font.size = Pt(9)
    return table


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    table.rows[0]._tr.get_or_add_trPr()
    for c, head in zip(table.rows[0].cells, headers):
        set_cell_shading(c, "1F4E79")
        set_cell_margins(c)
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(p.add_run(head), size=10, bold=True, color="FFFFFF")
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for c, value in zip(cells, row):
            if row_index % 2 == 1:
                set_cell_shading(c, "F4F8FC")
            set_cell_margins(c)
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            set_run_font(p.add_run(value), size=10)
    if widths:
        for row in table.rows:
            for cell, width in zip(row.cells, widths):
                cell.width = Inches(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


doc = Document()
section = doc.sections[0]
section.top_margin = Inches(0.75)
section.bottom_margin = Inches(0.7)
section.left_margin = Inches(0.8)
section.right_margin = Inches(0.8)

styles = doc.styles
styles["Normal"].font.name = "Microsoft YaHei"
styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
styles["Normal"].font.size = Pt(11)
for name, size in (("Title", 22), ("Heading 1", 15), ("Heading 2", 12)):
    styles[name].font.name = "Microsoft YaHei"
    styles[name]._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    styles[name].font.size = Pt(size)
    styles[name].font.color.rgb = RGBColor(0, 0, 0)

footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run_font(footer.add_run("Lab4 一层全连接计算模块 代码与仿真操作说明"), size=9, color="555555")

title = doc.add_paragraph(style="Title")
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run_font(title.add_run("Lab4 代码与仿真操作说明"), size=22, bold=True)
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run_font(sub.add_run("一层全连接计算模块的实现过程与当前状态"), size=12, color="555555")

add_text(doc, "本文记录本次 Lab4 从老师提供的 fc.v 框架开始，到创建 BRAM、乘法器阵列、顶层模块和测试平台的实际操作。目标是说明每一处代码为何存在、数据如何在模块间流动，以及当前仿真结果能说明什么。本文不将当前工程描述为已经通过验收，因为输出文件目前仍为空，尚未出现与参考值的完整比较结论。")

doc.add_heading("1 实验目标和计算对象", level=1)
add_text(doc, "Lab4 要在 FPGA 上实现一个全连接层。输入向量有 512 个 8 位有符号数，输出有 128 个通道，每个输出通道对应 512 个 8 位权重和 1 个 8 位偏置。单个输出的计算为 y[i] = ReLU(Σ(w[i][j] × x[j]) + b[i])。输出保留为 32 位，不做截位。")
add_text(doc, "为了同时使用 128 个乘法器，512 个输入被分成 4 组，每组 128 个数。对同一个输出通道，4 组部分和依次累加后才加偏置并做 ReLU。")

doc.add_heading("2 初始 fc.v 框架包含的接口", level=1)
add_table(doc,
          ["接口", "方向", "用途"],
          [
              ["input_data_addr_o / input_data_i", "fc 发地址，输入 RAM 回数据", "每次读取 128 个输入，共 4 行，每行 1024 位"],
              ["weight_addr_o / weight_i", "fc 发地址，权重 RAM 回数据", "读取当前输出通道和分组对应的 128 个权重"],
              ["bias_addr_o / bias_i", "fc 发地址，偏置 RAM 回数据", "读取当前输出通道的一个 8 位偏置"],
              ["mul_data1_o / mul_data2_o", "fc 输出", "将两组 1024 位数据交给乘法器阵列"],
              ["mul_result_i", "fc 输入", "接收 128 个 16 位乘积，共 2048 位"],
              ["fc_output_*", "fc 输出", "输出地址、32 位结果和写使能"],
          ], [1.9, 2.2, 3.4])
add_text(doc, "因此，fc.v 是控制与计算模块，不负责直接例化 BRAM 或单个乘法器 IP。BRAM、乘法器阵列和 fc 的实际接线放在 fc_top.v。")

doc.add_heading("3 对 fc.v 补充的控制逻辑", level=1)
add_text(doc, "补充的 group_idx 是内层循环计数器，取值 0 到 3。out_channel 是外层循环计数器，取值 0 到 127。group_idx 到 3 后回到 0，同时 out_channel 加一。running 用来标记一次计算正在进行。")
add_code(doc, "input_data_addr_o <= group_idx;\nweight_addr_o     <= {out_channel, 2'b00} + group_idx;\nbias_addr_o       <= out_channel;")
add_text(doc, "上面的地址公式与 COE 文件的数据布局对应。输入 RAM 仅有 4 行，所以地址就是分组号。每个输出通道在权重 RAM 中占 4 行，因此权重地址等于 out_channel × 4 + group_idx。偏置地址等于输出通道号。")
add_text(doc, "因为 BRAM、乘法器和加法树都有流水线延迟，代码增加 out_channel_dly 和 group_idx_dly 延迟链。第 9 拍延迟信号用于把加法树输出累加到对应通道；第 10 拍用于在第 4 组部分和完成后加偏置；第 12 拍用于生成输出地址、写使能和 done。")
add_table(doc,
          ["阶段", "对应代码动作", "使用的控制信号"],
          [
              ["1", "生成三类 RAM 地址", "group_idx，out_channel"],
              ["2 到 4", "BRAM 返回输入、权重、偏置", "RAM 的读延迟"],
              ["5 到 7", "128 路乘法器计算", "mult_8 的 3 级流水"],
              ["8 到 10", "加法树求一组 128 项的和", "adder_tree 的 3 级流水"],
              ["11", "写入或累加 channel_accum", "group_idx_dly[9]"],
              ["12 到 14", "加偏置、ReLU、写输出", "group_idx_dly[10] 和 [12]"],
          ], [0.7, 3.3, 3.5])

doc.add_heading("4 新建 adder_tree.v", level=1)
add_text(doc, "adder_tree.v 接收 mul_result_i 的 2048 位数据，并拆成 128 个 16 位乘积。采用两两相加的树形结构，避免把大量操作数放进同一个加法表达式。树被分为三级寄存器流水：128 到 32、32 到 4、4 到 1。最终 23 位有符号和被符号扩展到 32 位，接入 fc.v 的 final_sum。")
add_text(doc, "注意：fc.v 当前仍向 adder_tree 传入 DATA_WIDTH 和 NUM_INPUTS 两个参数，而现有 adder_tree 模块头没有声明这两个参数。Vivado 将其报告为警告，不会阻止展开。为消除警告，可以删除 fc.v 中这两个参数连接，或在 adder_tree 模块头显式增加同名参数。")

doc.add_heading("5 乘法器 IP 与 mult_array.v", level=1)
add_text(doc, "在 Vivado IP Catalog 中生成的 mult_8 是一个单独的 8 位乘法器，而不是 128 路阵列。它的端口为 CLK、A[7:0]、B[7:0]、SCLR 和 P[15:0]。因此，不能把 1024 位的 mul_data1 和 mul_data2 直接连接到一个 mult_8 实例。")
add_text(doc, "为匹配 fc.v 的总线接口，新建 mult_array.v。它用 generate 循环例化 128 个 mult_8，并将第 i 个 8 位数据切片接到第 i 个 IP。每个 IP 的 16 位输出被拼接到 result_o 的对应位置。SCLR 为高有效同步清零，因此接 ~rst_n_i。")
add_code(doc, "mult_8 u_mult_8 (\n    .CLK  (clk_i),\n    .A    (data1_i[1023 - i*8 -: 8]),\n    .B    (data2_i[1023 - i*8 -: 8]),\n    .SCLR (~rst_n_i),\n    .P    (result_o[2047 - i*16 -: 16])\n);")

doc.add_heading("6 新建 fc_top.v 及 BRAM 连接", level=1)
add_text(doc, "fc_top.v 是系统接线模块，例化 fc、4 个 Block Memory Generator IP 和 mult_array。模块关系如下。")
add_code(doc, "fc_input_ram  ─┐\nfc_weight_ram ─┼─> fc ── mul_data1_o / mul_data2_o ─> mult_array ─> mul_result_i\nfc_bias_ram   ─┘       │\n                         └─ fc_output_addr_o / data_o / wren_o ─> fc_output_ram")
add_text(doc, "本工程实际生成的 BRAM 均为单端口 RAM。单端口表示只有一组 A 端口，不表示只有一个信号。输入 RAM 和偏置 RAM 的实际模块接口包括 clka、rsta、wea、addra、dina、douta；权重和输出 RAM 不含 rsta。四个 IP 都不含 ena。")
add_table(doc,
          ["RAM", "配置", "顶层连接要点"],
          [
              ["fc_input_ram", "1024 位 × 4，COE 初始化", "wea=0，rsta 接 ~rst_n_i，douta 接 input_data"],
              ["fc_weight_ram", "1024 位 × 512，COE 初始化", "wea=0，douta 接 weight_data"],
              ["fc_bias_ram", "8 位 × 128，COE 初始化", "wea=0，rsta 接 ~rst_n_i，douta 接 bias_data"],
              ["fc_output_ram", "32 位 × 128", "wea 接 fc_output_wren_o，dina 接 fc_output_data_o"],
          ], [1.4, 2.2, 3.9])
add_text(doc, "曾经出现过顶层对 RAM 连接 .ena(1'b1) 的写法。检查生成的 IP wrapper 后确认它没有 ena 端口，因此该连接已删除。这个修正是 XSim 从“无法展开”变为“可以展开”的直接原因。")

doc.add_heading("7 新建 tb_fc_top.v", level=1)
add_text(doc, "测试平台例化 fc_top，产生 100 MHz 时钟，保持复位 5 个周期，再给 start_i 一个周期的启动脉冲。每当 fc_output_wren_o 为 1，测试平台就将 fc_output_data_o 写入 fc1_sim.txt，并从 fc1.txt 读一个参考数进行比较。")
add_table(doc,
          ["变量或信号", "作用", "用于判断"],
          [
              ["fc_output_wren_o", "表示当前输出有效", "只有为 1 时才记录和比较"],
              ["actual_value", "当前硬件结果", "来自 fc_output_data_o"],
              ["expected_value", "参考结果", "来自 fc1.txt"],
              ["error_num", "累计不匹配次数", "0 表示没有发现比较错误"],
              ["output_num", "已比较的输出数量", "应最终为 128"],
              ["done_o", "本次计算结束", "触发最终 PASS 或 FAIL 汇总"],
          ], [1.8, 2.8, 2.9])
add_text(doc, "设计的验收条件是 output_num 等于 128 且 error_num 等于 0。此时控制台会显示 PASS: all 128 FC outputs match fc1.txt。若有差异，控制台会显示对应的输出地址、实际值和参考值。")

doc.add_heading("8 当前仿真状态和需要继续检查的内容", level=1)
add_text(doc, "当前 XSim 已经成功完成编译与 elaboration，三个初始化 BRAM 也已加载数据。这说明顶层中的模块名、RAM IP、乘法器阵列与测试平台已能被仿真器识别。")
add_text(doc, "但是 fc1_sim.txt 当前为空，simulate.log 中也没有 PASS、FAIL 或 TIMEOUT 信息。因此现阶段只能确认仿真环境已启动，不能确认网络计算结果正确。需要在 Vivado 波形窗口点击 Run All，使仿真运行到 done_o。")
add_text(doc, "继续调试时应优先观察 start_i、running、group_idx、out_channel、input_data_addr_o、weight_addr_o、mul_result_i、final_sum、fc_output_wren_o、fc_output_addr_o、fc_output_data_o 和 done_o。若 fc_output_wren_o 一直为 0，应从 running 和延迟链开始检查；若写入次数不为 128，应检查 group_idx_dly[12] 的对齐。")
add_text(doc, "此外，fc.v 目前没有单独的 valid 延迟链。复位释放后的流水线空数据可能在 group_idx_dly 为 3 时触发写使能。若波形出现复位后过早写输出，建议新增 valid_dly，并将 fc_output_wren_o 和 done_o 与 valid_dly[12] 相与。是否需要这项修正，应以实际波形和 128 个输出比较结果为准。")

doc.add_heading("9 文件清单", level=1)
add_text(doc, "核心 HDL 文件包括 fc.v、adder_tree.v、mult_array.v、fc_top.v 和 tb_fc_top.v。fc1.txt 是参考输出；fc1_sim.txt 是测试平台自动生成的实际输出文件。四个 BRAM IP 的初始化文件分别来自 sel_data_128.coe、fc1.0.weight_128.coe 和 fc1.0.bias.coe。当前最重要的下一步是运行完整仿真，并以 128 个输出、error_num 和参考文件比较结果验证时序对齐。")

doc.save(OUT)
print(OUT)
