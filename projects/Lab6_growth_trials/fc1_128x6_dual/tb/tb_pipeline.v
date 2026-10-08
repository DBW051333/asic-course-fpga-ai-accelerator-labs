`timescale 1ns/1ps
// One request, sample 0. Observe outputs after NBA updates; write strobes
// below record enables sampled AT the clock edge, before NBA updates.
module tb_pipeline;
    parameter real CLK_PERIOD = 4.09;
    reg clk = 0, reset_n = 0, start = 0;
    always #(CLK_PERIOD/2) clk = ~clk;
    wire ready, done;
    wire fc1_valid, fc2_valid, fc3_valid;
    wire [7:0] fc1_data, fc2_data0, fc2_data1, fc2_data2, fc2_data3, fc3_data;
    wire [6:0] fc1_addr;
    wire [4:0] fc2_addr;
    wire fc3_addr;
    reg fc2_sum_write = 0, fc3_sum_write = 0;
    wire fc2_merge = dut.u_fc2.merge_pending;
    wire fc2_snapshot = dut.u_fc2.snapshot_pending;
    wire signed [20:0] fc2_even0 = dut.u_fc2.interleaved[0].even_acc;
    wire signed [20:0] fc2_odd0 = dut.u_fc2.interleaved[0].odd_acc;
    wire signed [20:0] fc2_result0 = dut.u_fc2.snapshot[0];
    wire signed [18:0] fc3_sum0 = dut.u_fc3.acc[0];
    lab5_top dut(
        .clk_i(clk), .rst_n_i(reset_n), .start_i(start), .ready_o(ready), .done_o(done),
        .fc1_wren_o(fc1_valid), .fc1_data_o(fc1_data), .fc1_addr_o(fc1_addr),
        .fc2_wren_o(fc2_valid), .fc2_data_o(fc2_data0), .fc2_data_b_o(fc2_data1),
        .fc2_data_c_o(fc2_data2), .fc2_data_d_o(fc2_data3), .fc2_addr_o(fc2_addr),
        .fc3_wren_o(fc3_valid), .fc3_data_o(fc3_data), .fc3_addr_o(fc3_addr));
    reg [7:0] inputs_all[0:24575];
    reg signed [63:0] ref1[0:6143], ref2[0:1535], ref3[0:95];
    integer g,l,cycle=-1,n1=0,n2=0,n3=0,errors=0;
    integer first_sum2=-1,first_sum3=-1,last_fc1=-1;
    // Observe actual FC1 DSP lane 0, including its four-edge operand-to-product pipeline.
    wire signed [24:0] pack_weight = dut.u_fc1.packed_w[0];
    wire signed [7:0] pack_input = dut.u_fc1.input_p[0];
    wire signed [32:0] pack_result = dut.u_fc1.product_r[0];
    wire signed [15:0] pack_low_actual = dut.u_fc1.low_product[0];
    wire signed [15:0] pack_high_actual = dut.u_fc1.high_product[0];
    reg pack_check_valid=0;
    reg signed [7:0] pack_x_used=0,pack_w0_used=0,pack_w1_used=0;
    reg signed [15:0] pack_low_expected=0,pack_high_expected=0;
    reg signed [16:0] pack_high_raw=0;
    reg pack_correction=0;
    reg signed [7:0] pack_x_queue[0:3],pack_w0_queue[0:3],pack_w1_queue[0:3];
    reg [3:0] pack_known=0;
    integer pack_checks=0,pack_negative_checks=0,pk;
    reg signed [7:0] operand_w0,operand_w1;
    always @(posedge clk) begin
        pack_check_valid = reset_n && pack_known[3];
        if(pack_check_valid) begin
            pack_x_used=pack_x_queue[3];
            pack_w0_used=pack_w0_queue[3];
            pack_w1_used=pack_w1_queue[3];
            pack_low_expected=$signed(pack_x_used)*$signed(pack_w0_used);
            pack_high_expected=$signed(pack_x_used)*$signed(pack_w1_used);
            // Capture the wide result used by this edge's splitting logic.
            pack_high_raw=$signed(dut.u_fc1.product_r[0][32:16]);
            pack_correction=dut.u_fc1.product_r[0][15];
        end
        operand_w0=pack_weight[7:0];
        operand_w1=$signed(pack_weight[24:16])+pack_weight[7];
        pack_x_queue[0]<=pack_input;
        pack_w0_queue[0]<=operand_w0;
        pack_w1_queue[0]<=operand_w1;
        for(pk=1;pk<4;pk=pk+1) begin
            pack_x_queue[pk]<=pack_x_queue[pk-1];
            pack_w0_queue[pk]<=pack_w0_queue[pk-1];
            pack_w1_queue[pk]<=pack_w1_queue[pk-1];
        end
        pack_known<={pack_known[2:0], reset_n && ((^pack_input)!==1'bx) && ((^pack_weight)!==1'bx)};
        #0.004;
        if(pack_check_valid) begin
            if(pack_low_actual!==pack_low_expected || pack_high_actual!==pack_high_expected) begin
                errors=errors+1;
                $display("PACK_FAIL x=%0d w0=%0d w1=%0d expected=%0d,%0d actual=%0d,%0d",pack_x_used,pack_w0_used,pack_w1_used,pack_low_expected,pack_high_expected,pack_low_actual,pack_high_actual);
            end
            pack_checks=pack_checks+1;
            if(pack_correction)pack_negative_checks=pack_negative_checks+1;
            if(pack_checks<=4 || (pack_correction && pack_negative_checks<=2))
                $display("PACK_DATA x=%0d w0=%0d w1=%0d low=%0d high_raw=%0d correction=%0d high=%0d",pack_x_used,pack_w0_used,pack_w1_used,pack_low_actual,pack_high_raw,pack_correction,pack_high_actual);
        end
    end
    // FC1 issue signals record the operation accepted at this edge.
    reg fc1_issue_valid=0, fc1_group_valid=0;
    integer fc1_issue_pair=-1, fc1_issue_group=-1;
    integer fc1_compute_pair=-1, fc1_compute_group=-1;
    integer fc1_issue_count=0, fc1_group_count=0;
    reg signed [31:0] fc1_group_sum0=0, fc1_group_sum1=0;
    wire signed [22:0] fc1_acc0 = dut.u_fc1.acc0;
    wire signed [22:0] fc1_acc1 = dut.u_fc1.acc1;
    wire signed [22:0] fc1_pair_result0 = dut.u_fc1.pair0;
    wire signed [22:0] fc1_pair_result1 = dut.u_fc1.pair1;
    always @(posedge clk) begin
        fc1_issue_valid = reset_n && dut.u_fc1.running;
        fc1_group_valid = reset_n && dut.u_fc1.valid_pipe[15];
        if(fc1_issue_valid) begin
            fc1_issue_pair = dut.u_fc1.issue_pair;
            fc1_issue_group = dut.u_fc1.issue_group;
            if(fc1_issue_pair!=fc1_issue_count/2 || fc1_issue_group!=fc1_issue_count%2)errors=errors+1;
            if(fc1_issue_count<6 || fc1_issue_count>=126)
                $display("FC1 ISSUE step=%0d neurons=%0d,%0d group=%0d inputs=%0d..%0d",fc1_issue_count,2*fc1_issue_pair,2*fc1_issue_pair+1,fc1_issue_group,256*fc1_issue_group,256*fc1_issue_group+255);
            fc1_issue_count=fc1_issue_count+1;
        end
        if(fc1_group_valid) begin
            fc1_compute_pair = dut.u_fc1.tag[15][7:2];
            fc1_compute_group = dut.u_fc1.tag[15][1:0];
            fc1_group_sum0 = $signed(dut.u_fc1.group_sum0);
            fc1_group_sum1 = $signed(dut.u_fc1.group_sum1);
            if(fc1_compute_pair!=fc1_group_count/2 || fc1_compute_group!=fc1_group_count%2)errors=errors+1;
            fc1_group_count=fc1_group_count+1;
            #0.003;
            if(fc1_compute_pair<2) begin
                if(fc1_compute_group==0)
                    $display("FC1 DATA pair=%0d group0 sums=%0d,%0d accum_with_bias=%0d,%0d",fc1_compute_pair,fc1_group_sum0,fc1_group_sum1,fc1_acc0,fc1_acc1);
                else
                    $display("FC1 DATA pair=%0d group1 sums=%0d,%0d completed=%0d,%0d",fc1_compute_pair,fc1_group_sum0,fc1_group_sum1,fc1_pair_result0,fc1_pair_result1);
            end
        end
    end
    reg active=0;
    // Independent unpacked weights; never use DUT's packed ROM for expected sums.
    reg [255:0] reference_weights[0:127];
    reg [7:0] reference_bias[0:31];
    integer product_checks=0, sum_checks=0, snapshot_checks=0;
    integer data_fd;
    reg data_step_valid=0;
    integer data_input_index=-1;
    reg signed [63:0] expected_x0=0, expected_w0=0, expected_product0=0;
    reg signed [63:0] expected_even0=0, expected_odd0=0;
    reg signed [15:0] product_to_write0=0, observed_product0=0;
    initial begin
        $readmemh("/home/ding/vivado_project/Lab5_optimization/data/fc2_weights.mem",reference_weights);
        $readmemh("/home/ding/vivado_project/Lab5_optimization/data/fc2_bias.mem",reference_bias);
        data_fd=$fopen("/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/results/pipeline_data.csv","w");
        $fdisplay(data_fd,"cycle,input_index,x,weight,expected_product,observed_product,expected_even,actual_even,expected_odd,actual_odd");
    end
    always @(posedge clk) begin
        data_step_valid <= reset_n && dut.u_fc2.valid_after;
        if(reset_n && dut.u_fc2.valid_pipe[4]) product_to_write0 <= dut.u_fc2.product_r[0];
        if(reset_n && dut.u_fc2.valid_after) observed_product0 <= product_to_write0;
    end
    genvar channel;
    generate for(channel=0;channel<32;channel=channel+1) begin:data_check
        integer product_index=0, sum_index=0;
        reg signed [63:0] expected_even=0, expected_odd=0;
        reg signed [63:0] x,w,term,merged,px,pw,pterm;
        always @(posedge clk) begin
            if(reset_n && dut.u_fc2.valid_pipe[4]) begin
                px=ref1[product_index];
                pw=$signed(reference_weights[product_index][255-channel*8 -:8]);
                pterm=px*pw;
                if($signed(dut.u_fc2.product_r[channel])!==pterm) begin
                    errors=errors+1;
                    $display("DATA_FAIL product channel=%0d input=%0d",channel,product_index);
                end
                product_checks=product_checks+1;
                product_index=product_index+1;
            end
        end
        always @(posedge clk) begin
            if(reset_n && dut.u_fc2.valid_after) begin
                x=ref1[sum_index];
                w=$signed(reference_weights[sum_index][255-channel*8 -:8]);
                term=x*w;
                if(sum_index==0) expected_even=$signed(reference_bias[channel])+term;
                else if(sum_index%2==0) expected_even=expected_even+term;
                else expected_odd=expected_odd+term;
                if(channel==0) begin
                    data_input_index=sum_index; expected_x0=x; expected_w0=w; expected_product0=term;
                    expected_even0=expected_even; expected_odd0=expected_odd;
                end
                #0.002;
                if(sum_index%2==0) begin
                    if($signed(dut.u_fc2.interleaved[channel].even_acc)!==expected_even)errors=errors+1;
                end else begin
                    if($signed(dut.u_fc2.interleaved[channel].odd_acc)!==expected_odd)errors=errors+1;
                end
                sum_checks=sum_checks+1;
                if(channel==0) begin
                    $fdisplay(data_fd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",cycle,sum_index,x,w,term,observed_product0,expected_even,fc2_even0,expected_odd,fc2_odd0);
                    if(sum_index<4 || sum_index>=126)
                        $display("DATA input=%0d x=%0d w=%0d product=%0d actual_product=%0d even=%0d odd=%0d",sum_index,x,w,term,observed_product0,fc2_even0,fc2_odd0);
                end
                sum_index=sum_index+1;
            end
        end
        always @(posedge clk) begin
            if(reset_n && dut.u_fc2.snapshot_pending) begin
                merged=expected_even+expected_odd;
                #0.002;
                if($signed(dut.u_fc2.snapshot[channel])!==merged)errors=errors+1;
                snapshot_checks=snapshot_checks+1;
                if(channel==0) $display("DATA FC2 channel0 merged=%0d actual=%0d ReLU=%0d quantized=%0d",merged,fc2_result0,(merged<0?0:merged),ref2[0]);
            end
        end
    end endgenerate
    initial begin
        $readmemh("/home/ding/vivado_project/Lab5_truncation_optimization/data/all_inputs.mem", inputs_all);
        $readmemh("/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/data/fc1_expected.mem",ref1);
        $readmemh("/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/data/fc2_expected.mem",ref2);
        $readmemh("/home/ding/vivado_project/Lab6_growth_trials/fc1_128x6_dual/data/fc3_expected.mem",ref3);
        repeat(5) @(negedge clk);
        for(g=0;g<2;g=g+1)
            for(l=0;l<256;l=l+1)
                dut.u_fc1.inputs[g][2047-l*8 -:8]=inputs_all[g*256+l];
        reset_n=1; start=1;
        @(negedge clk); start=0;
    end
    always @(posedge clk) begin
        fc2_sum_write = reset_n && dut.u_fc2.valid_after;
        fc3_sum_write = reset_n && dut.u_fc3.valid_pipe[5];
        if(reset_n && start && ready) begin active=1; cycle=-1; end
        if(active) begin
            cycle=cycle+1;
            #0.001;
            if(cycle==0) $display("PIPE cycle=0 START");
            if(fc1_valid) begin
                if(fc1_addr!==n1 || $signed(fc1_data)!==ref1[n1]) errors=errors+1;
                if(n1==0 || n1==127) $display("PIPE cycle=%0d FC1 output addr=%0d",cycle,fc1_addr);
                if(n1==127)last_fc1=cycle;
                n1=n1+1;
            end
            if(fc2_sum_write && first_sum2<0) begin
                first_sum2=cycle;
                $display("PIPE cycle=%0d FC2 first partial-sum write; FC1 outputs so far=%0d",cycle,n1);
            end
            if(fc2_valid) begin
                if(fc2_addr!==n2 || $signed(fc2_data0)!==ref2[n2] ||
                   $signed(fc2_data1)!==ref2[n2+1] || $signed(fc2_data2)!==ref2[n2+2] ||
                   $signed(fc2_data3)!==ref2[n2+3]) errors=errors+1;
                $display("PIPE cycle=%0d FC2 output group addr=%0d..%0d",cycle,fc2_addr,fc2_addr+3);
                n2=n2+4;
            end
            if(fc3_sum_write && first_sum3<0) begin
                first_sum3=cycle;
                $display("PIPE cycle=%0d FC3 first partial-sum write; FC2 outputs so far=%0d",cycle,n2);
            end
            if(fc3_valid) begin
                if(fc3_addr!==(n3%2) || $signed(fc3_data)!==ref3[n3])errors=errors+1;
                $display("PIPE cycle=%0d FC3 output addr=%0d score=%0d",cycle,fc3_addr,$signed(fc3_data));
                n3=n3+1;
            end
            if(done) begin
                if(n1!=128 || n2!=32 || n3!=2 || cycle!=174 || first_sum2>=last_fc1)errors=errors+1;
                $display("PIPE DONE latency=%0d cycles counts=%0d/%0d/%0d errors=%0d",cycle,n1,n2,n3,errors);
                if(pack_checks==0 || pack_negative_checks==0)errors=errors+1;
                $display("PACK CHECK lane0 comparisons=%0d negative_low_cases=%0d errors=%0d",pack_checks,pack_negative_checks,errors);
                if(fc1_issue_count!=128 || fc1_group_count!=128)errors=errors+1;
                $display("FC1 CHECK issue_steps=%0d completed_groups=%0d output_pairs=%0d",fc1_issue_count,fc1_group_count,n1/2);
                if(product_checks!=4096 || sum_checks!=4096 || snapshot_checks!=32)errors=errors+1;
                $fclose(data_fd);
                $display("DATA CHECK products=%0d partial_sums=%0d snapshots=%0d errors=%0d",product_checks,sum_checks,snapshot_checks,errors);
                if(errors) $fatal(1,"Pipeline check failed");
                $display("PASS: sample 0, all 162 outputs match; FC2 starts before FC1 finishes");
                active=0;
                #20; $finish;
            end
        end
    end
    initial begin #2000; $fatal(1,"Pipeline simulation timeout"); end
endmodule
