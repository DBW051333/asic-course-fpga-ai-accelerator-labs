`timescale 1ns / 1ps

module tb_lab5_top;
    parameter CLK_PERIOD = 10;
    reg clk_i = 1'b0;
    reg rst_n_i = 1'b0;
    reg start_i = 1'b0;
    wire done_o;
    wire fc1_wren, fc2_wren, fc3_wren;
    wire [31:0] fc1_data;
    wire [47:0] fc2_data;
    wire [63:0] fc3_data;
    wire [6:0] fc1_addr;
    wire [4:0] fc2_addr;
    wire fc3_addr;
    integer fd1, fd2, fd3, ref1, ref2, ref3;
    integer got1, got2, got3, errors, scan;
    reg signed [63:0] expected;
    reg signed [63:0] actual;

    lab5_top dut (
        .clk_i(clk_i), .rst_n_i(rst_n_i), .start_i(start_i), .done_o(done_o),
        .fc1_wren_o(fc1_wren), .fc1_data_o(fc1_data), .fc1_addr_o(fc1_addr),
        .fc2_wren_o(fc2_wren), .fc2_data_o(fc2_data), .fc2_addr_o(fc2_addr),
        .fc3_wren_o(fc3_wren), .fc3_data_o(fc3_data), .fc3_addr_o(fc3_addr)
    );

    always #(CLK_PERIOD/2) clk_i = ~clk_i;

    initial begin
        got1 = 0; got2 = 0; got3 = 0; errors = 0;
        fd1 = $fopen("/home/ding/vivado_project/Lab5/results/fc1_sim.txt", "w");
        fd2 = $fopen("/home/ding/vivado_project/Lab5/results/fc2_sim.txt", "w");
        fd3 = $fopen("/home/ding/vivado_project/Lab5/results/fc3_sim.txt", "w");
        ref1 = $fopen("/home/ding/vivado_project/Lab5/data/reference/fc1.txt", "r");
        ref2 = $fopen("/home/ding/vivado_project/Lab5/data/reference/fc2.txt", "r");
        ref3 = $fopen("/home/ding/vivado_project/Lab5/data/reference/fc3.txt", "r");
        if (fd1 == 0 || fd2 == 0 || fd3 == 0 || ref1 == 0 || ref2 == 0 || ref3 == 0) begin
            $display("ERROR: cannot open Lab5 result or reference files");
            $finish;
        end
        repeat (5) @(negedge clk_i);
        rst_n_i = 1'b1;
        @(negedge clk_i); start_i = 1'b1;
        @(negedge clk_i); start_i = 1'b0;
    end

    task compare_value;
        input signed [63:0] data;
        input integer ref_fd;
        input integer index;
        input [8*3-1:0] name;
        begin
            actual = data;
            scan = $fscanf(ref_fd, "%d", expected);
            if (scan != 1 || actual !== expected) begin
                $display("MISMATCH %s[%0d]: actual=%0d expected=%0d", name, index, actual, expected);
                errors = errors + 1;
            end
        end
    endtask

    always @(posedge clk_i) begin
        if (rst_n_i && fc1_wren) begin
            $fwrite(fd1, "%0d\n", $signed(fc1_data));
            compare_value({{32{fc1_data[31]}}, fc1_data}, ref1, got1, "FC1");
            got1 = got1 + 1;
        end
        if (rst_n_i && fc2_wren) begin
            $fwrite(fd2, "%0d\n", $signed(fc2_data));
            compare_value({{16{fc2_data[47]}}, fc2_data}, ref2, got2, "FC2");
            got2 = got2 + 1;
        end
        if (rst_n_i && fc3_wren) begin
            $fwrite(fd3, "%0d\n", $signed(fc3_data));
            compare_value(fc3_data, ref3, got3, "FC3");
            got3 = got3 + 1;
        end
    end

    initial begin
        wait (done_o);
        repeat (3) @(posedge clk_i);
        if (got1 != 128 || got2 != 32 || got3 != 2) begin
            $display("FAIL: output counts FC1=%0d FC2=%0d FC3=%0d", got1, got2, got3);
            errors = errors + 1;
        end
        if (errors == 0) $display("PASS: FC1/FC2/FC3 all match reference outputs");
        else $display("FAIL: %0d mismatch(es)", errors);
        $fclose(fd1); $fclose(fd2); $fclose(fd3);
        $fclose(ref1); $fclose(ref2); $fclose(ref3);
        #20 $finish;
    end

    initial begin
        #(CLK_PERIOD * 20000);
        $display("TIMEOUT: Lab5 did not complete");
        $finish;
    end
endmodule
