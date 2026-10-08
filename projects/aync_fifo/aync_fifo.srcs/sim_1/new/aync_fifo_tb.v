`timescale 1ns / 1ps

module aync_fifo_tb #(
    parameter data_width = 16,
    parameter addr_width = 5
);

    reg rst_n;

    reg wr_clk, wr_en;
    reg [data_width-1:0] wr_data;

    reg rd_clk, rd_en;

    wire valid;
    wire [data_width-1:0] rd_data;
    wire empty, full;

    // Adapted to the module and port names in aync_fifo.v.
    aync_fifo aync_fifo (
        .rst_n  (rst_n),
        .wr_clk (wr_clk),
        .wr_en  (wr_en),
        .wr_data(wr_data),
        .rd_clk (rd_clk),
        .rd_en  (rd_en),
        .valid  (valid),
        .rd_data(rd_data),
        .full   (full),
        .empty  (empty)
    );

    initial begin
        wr_clk = 1;
        forever #5 wr_clk = ~wr_clk;
    end

    initial begin
        rd_clk = 1;
        forever #10 rd_clk = ~rd_clk;
    end

    initial begin
        rst_n   = 'd1;
        rd_en   = 'd0;
        wr_en   = 'd0;
        wr_data = 'd0;
        #50 rst_n = 'd0;
        #50 rst_n = 'd1;
    end

    reg [data_width-1:0] input_data [0:9];
    initial begin
        #500;
        $readmemb("/home/ding/vivado_project/aync_fifo/input_asy_data_b.txt", input_data);
    end

    integer cnt_rd_data;
    integer fp_rd_data;
    initial begin
        cnt_rd_data = 0;
        fp_rd_data = $fopen("/home/ding/vivado_project/aync_fifo/output_asy_data_b.txt", "w");
    end

    integer ii;
    initial begin
        #1000;
        for (ii = 0; ii < 10; ii = ii + 1) begin
            @(negedge wr_clk) begin
                wr_en   <= 'd1;
                wr_data <= input_data[ii];
            end
            @(negedge wr_clk) begin
                wr_en <= 'd0;
            end
            repeat (10) @(negedge wr_clk);
        end

        for (ii = 0; ii < 10; ii = ii + 1) begin
            @(negedge rd_clk) begin
                rd_en <= 'd1;
            end
            @(negedge rd_clk) begin
                rd_en <= 'd0;
            end
            repeat (10) @(negedge rd_clk);
        end
    end

    always @(negedge rd_clk) begin
        if (aync_fifo.valid) begin
            cnt_rd_data <= cnt_rd_data + 'd1;
            if (cnt_rd_data == 'd9) begin
                $fclose(fp_rd_data);
            end
            $fwrite(fp_rd_data, "%b\n", $signed(aync_fifo.rd_data));
        end
    end

endmodule
