`timescale 1ns / 1ps

// Lab4 行为仿真测试平台。
// 运行仿真前，将 REFERENCE_FILE 改为 fc1.txt 在仿真工作目录中的实际路径，
// 或在 Vivado 的 Simulation Settings 中将该文件复制到仿真运行目录。
module tb_fc_top;

    parameter CLK_PERIOD     = 10;
    parameter OUTPUT_FILE    = "/home/ding/vivado_project/Lab4_tree4/fc1_sim.txt";
    parameter REFERENCE_FILE = "/home/ding/vivado_project/Lab4_optimized/fc1.txt";
    parameter OUTPUT_COUNT   = 128;

    reg  clk_i;
    reg  rst_n_i;
    reg  start_i;
    wire done_o;

    wire        fc_output_wren_o;
    wire [31:0] fc_output_data_o;
    wire [6:0]  fc_output_addr_o;

    integer output_fd;
    integer reference_fd;
    integer scan_result;
    integer expected_value;
    integer actual_value;
    integer output_num;
    integer error_num;
    time start_time;

    always @(posedge start_i)
        start_time = $time;

    fc_top dut (
        .clk_i              (clk_i),
        .rst_n_i            (rst_n_i),
        .start_i            (start_i),
        .done_o             (done_o),
        .fc_output_wren_o   (fc_output_wren_o),
        .fc_output_data_o   (fc_output_data_o),
        .fc_output_addr_o   (fc_output_addr_o)
    );

    // 100 MHz 时钟。
    initial begin
        clk_i = 1'b0;
        forever #(CLK_PERIOD / 2) clk_i = ~clk_i;
    end

    // 打开输出文件与参考文件，再完成复位和一次计算启动。
    initial begin
        rst_n_i    = 1'b0;
        start_i    = 1'b0;
        output_num = 0;
        error_num  = 0;

        output_fd = $fopen(OUTPUT_FILE, "w");
        if (output_fd == 0) begin
            $display("ERROR: cannot open output file: %s", OUTPUT_FILE);
            $finish;
        end

        reference_fd = $fopen(REFERENCE_FILE, "r");
        if (reference_fd == 0) begin
            $display("ERROR: cannot open reference file: %s", REFERENCE_FILE);
            $display("Please set REFERENCE_FILE to the location of fc1.txt.");
            $fclose(output_fd);
            $finish;
        end

        repeat (5) @(negedge clk_i);
        rst_n_i = 1'b1;

        // start_i 只保持一个时钟周期。
        @(negedge clk_i);
        start_i = 1'b1;
        @(negedge clk_i);
        start_i = 1'b0;
    end

    // 每当 fc 写输出 RAM 时，保存数据并与 fc1.txt 对比。
    // 在时钟上升沿读取的是本周期稳定的写使能、地址与数据。
    always @(posedge clk_i) begin
        if (rst_n_i && fc_output_wren_o) begin
            actual_value = $signed(fc_output_data_o);
            $fwrite(output_fd, "%0d\n", actual_value);

            scan_result = $fscanf(reference_fd, "%d", expected_value);
            if (scan_result != 1) begin
                $display("ERROR: reference file ended at output %0d", output_num);
                error_num = error_num + 1;
            end else if (actual_value !== expected_value) begin
                $display("MISMATCH: addr=%0d, actual=%0d, expected=%0d",
                         fc_output_addr_o, actual_value, expected_value);
                error_num = error_num + 1;
            end

            output_num = output_num + 1;
        end
    end

    // done 到达后给最后一级流水和监视器一个周期，再汇总结果。
    initial begin
        wait (done_o == 1'b1);
        repeat (2) @(posedge clk_i);

        if (output_num != OUTPUT_COUNT) begin
            $display("ERROR: received %0d outputs, expected %0d",
                     output_num, OUTPUT_COUNT);
            error_num = error_num + 1;
        end

        $display("MEASURE: start_to_check=%0d ns, clock_period=%0d ns", $time - start_time, CLK_PERIOD);
        if (error_num == 0)
            $display("PASS: all %0d FC outputs match fc1.txt", OUTPUT_COUNT);
        else
            $display("FAIL: %0d error(s) found", error_num);

        $fclose(output_fd);
        $fclose(reference_fd);
        #20;
        $finish;
    end

    // 防止控制逻辑未完成时仿真无限运行。
    initial begin
        #(CLK_PERIOD * 10000);
        $display("TIMEOUT: done_o was not asserted.");
        $fclose(output_fd);
        $fclose(reference_fd);
        $finish;
    end

endmodule
