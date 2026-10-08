`timescale 1ns/1ps
module tb_lab6_top;
    parameter integer WIDTH = 8;
    parameter real CLK_PERIOD = 10;
    reg clk_i=0, rst_n_i=0, start_i=0, input_we_i=0;
    reg [1:0] input_addr_i=0;
    reg [1023:0] input_data_i=0;
    wire done_o, fc1_wren, fc2_wren, fc3_wren;
    wire [WIDTH-1:0] fc1_data, fc2_data, fc3_data;
    wire [6:0] fc1_addr;
    wire [4:0] fc2_addr, fc3_addr;
    reg [1023:0] samples [0:167];
    reg [WIDTH-1:0] exp1 [0:5375], exp2 [0:1343], exp3 [0:83];
    reg labels [0:41];
    integer sample_idx=0, got1=0, got2=0, got3=0, errors=0, correct=0;
    integer i, k, result_fd, pred;
    reg signed [WIDTH-1:0] score0, score1;

    realtime launched;integer latency_cycles,min_latency=99999,max_latency=0;
    lab6_top #(.WIDTH(WIDTH)) dut (
        .clk_i(clk_i), .rst_n_i(rst_n_i), .start_i(start_i),
        .input_we_i(input_we_i), .input_addr_i(input_addr_i), .input_data_i(input_data_i),
        .done_o(done_o),
        .fc1_wren_o(fc1_wren), .fc1_data_o(fc1_data), .fc1_addr_o(fc1_addr),
        .fc2_wren_o(fc2_wren), .fc2_data_o(fc2_data), .fc2_addr_o(fc2_addr),
        .fc3_wren_o(fc3_wren), .fc3_data_o(fc3_data), .fc3_addr_o(fc3_addr)
    );
    always #(CLK_PERIOD/2) clk_i=~clk_i;

    initial begin
        $readmemb("/home/ding/vivado_project/Lab6/data/samples_128.mem", samples);
        $readmemh("/home/ding/vivado_project/Lab6/data/labels.mem", labels);
        if (WIDTH==8) begin
            $readmemh("/home/ding/vivado_project/Lab6/data/fc1_expected_8.mem", exp1);
            $readmemh("/home/ding/vivado_project/Lab6/data/fc2_expected_8.mem", exp2);
            $readmemh("/home/ding/vivado_project/Lab6/data/fc3_expected_8.mem", exp3);
            result_fd=$fopen("/home/ding/vivado_project/Lab6_three_version_comparison/original_int8/results/rtl_8.csv","w");
        end else begin
            $readmemh("/home/ding/vivado_project/Lab6/data/fc1_expected_4.mem", exp1);
            $readmemh("/home/ding/vivado_project/Lab6/data/fc2_expected_4.mem", exp2);
            $readmemh("/home/ding/vivado_project/Lab6/data/fc3_expected_4.mem", exp3);
            result_fd=$fopen("/home/ding/vivado_project/Lab6/results/rtl_4.csv","w");
        end
        if (result_fd==0) $fatal(1,"cannot open result file");
        $fwrite(result_fd,"sample,score0,score1,prediction,label,correct\n");
        for (i=0;i<42;i=i+1) begin
            sample_idx=i; got1=0; got2=0; got3=0; score0=0; score1=0;
            rst_n_i=0; start_i=0; input_we_i=0;
            repeat(5) @(negedge clk_i);
            rst_n_i=1;
            for (k=0;k<4;k=k+1) begin
                input_we_i=1; input_addr_i=k; input_data_i=samples[i*4+k];
                @(negedge clk_i);
            end
            input_we_i=0;
            repeat(3) @(negedge clk_i);
            start_i=1; launched=$realtime+CLK_PERIOD/2;
            @(negedge clk_i); start_i=0;
            wait(done_o);
            repeat(3) @(negedge clk_i);
            if (got1!=128 || got2!=32 || got3!=2) begin
                $display("COUNT MISMATCH sample=%0d: %0d %0d %0d",i,got1,got2,got3);
                errors=errors+1;
            end
            pred=(score0<score1) ? 1 : 0;
            if (pred==labels[i]) correct=correct+1;
            $fwrite(result_fd,"%0d,%0d,%0d,%0d,%0d,%0d\n",i,score0,score1,pred,labels[i],pred==labels[i]);
            $display("sample=%0d width=%0d scores=(%0d,%0d) pred=%0d label=%0d",i,WIDTH,score0,score1,pred,labels[i]);
        end
        $display("PERFORMANCE latency_cycles=%0d..%0d",min_latency,max_latency);
        $fclose(result_fd);
        $display("SUMMARY width=%0d accuracy=%0d/42 mismatches=%0d",WIDTH,correct,errors);
        if (errors) $fatal(1,"RTL differs from integer reference");
        $finish;
    end

    always @(posedge clk_i) begin
        if (rst_n_i && fc1_wren) begin
            if (fc1_data !== exp1[sample_idx*128+got1] || fc1_addr!=got1) begin
                $display("FC1 MISMATCH sample=%0d index=%0d got=%0d exp=%0d addr=%0d",sample_idx,got1,$signed(fc1_data),$signed(exp1[sample_idx*128+got1]),fc1_addr);
                errors=errors+1;
            end
            got1=got1+1;
        end
        if (rst_n_i && fc2_wren) begin
            if (fc2_data !== exp2[sample_idx*32+got2] || fc2_addr!=got2) begin
                $display("FC2 MISMATCH sample=%0d index=%0d got=%0d exp=%0d addr=%0d",sample_idx,got2,$signed(fc2_data),$signed(exp2[sample_idx*32+got2]),fc2_addr);
                errors=errors+1;
            end
            got2=got2+1;
        end
        if (rst_n_i && fc3_wren) begin
            if (fc3_data !== exp3[sample_idx*2+got3] || fc3_addr!=got3) begin
                $display("FC3 MISMATCH sample=%0d index=%0d got=%0d exp=%0d addr=%0d",sample_idx,got3,$signed(fc3_data),$signed(exp3[sample_idx*2+got3]),fc3_addr);
                errors=errors+1;
            end
            
            if (got3==0) score0=$signed(fc3_data);
            else score1=$signed(fc3_data);
            got3=got3+1;
        end
    end
    always @(posedge done_o)begin latency_cycles=$rtoi(($realtime-launched)/CLK_PERIOD+0.5);if(latency_cycles<min_latency)min_latency=latency_cycles;if(latency_cycles>max_latency)max_latency=latency_cycles;end
    initial begin
        #(CLK_PERIOD*500000);
        $fatal(1,"TIMEOUT");
    end
endmodule
