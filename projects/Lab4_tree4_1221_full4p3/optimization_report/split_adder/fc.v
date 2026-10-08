//本module实现的是全连接网络第一层，输入通道512，输出通道128。
//为提高计算效率，每次输入数据为1024位，即128维，进行128个并行乘法，4次即可完成一个输出通道的计算
//不做截位处理
module fc (
    input  wire        clk_i,
    input  wire        rst_n_i,
    input  wire        start_i,
    output wire        done_o,

    output reg  [1:0]  input_data_addr_o,
    input  wire [1023:0] input_data_i,

    output reg  [8:0]  weight_addr_o,
    input  wire [1023:0] weight_i,

    output reg  [6:0]  bias_addr_o,
    input  wire [7:0]  bias_i,

    output reg         fc_output_wren_o,
    output reg [31:0]  fc_output_data_o,
    output reg [6:0]   fc_output_addr_o,

    output wire [1023:0] mul_data1_o,
    output wire [1023:0] mul_data2_o,
    input  wire [2047:0] mul_result_i

);

    parameter INPUT_DIM  = 512;
    parameter OUTPUT_DIM = 128;
    parameter GROUPS     = 4;           // 输入分组数 (512/128)

    reg [6:0] out_channel;              // 输出通道 (0 ~ 127)
    reg [1:0] group_idx;                // 输入分组 (0 ~ 3)

    reg [6:0] out_channel_dly [0:14];   // 延迟链
    reg [1:0] group_idx_dly   [0:14];   // 延迟链

    reg [31:0] accumulator;
    wire [31:0] final_sum;
    reg [31:0] channel_accum;

    reg       running;
    reg       finish_r;

    integer   i;

    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            group_idx <= 0;
        end else begin
        if (start_i && !running) begin
        group_idx <= 2'd0;
    end else if (running) begin
        if (group_idx == GROUPS - 1)
            group_idx <= 2'd0;
        else
            group_idx <= group_idx + 1'b1;
    end
            //更新group_idx
        end
    end
    
    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            out_channel <= 0;
        end else begin
        if (start_i && !running) begin
        out_channel <= 7'd0;
    end else if (running && group_idx == GROUPS - 1) begin
        if (out_channel == OUTPUT_DIM - 1)
            out_channel <= 7'd0;
        else
            out_channel <= out_channel + 1'b1;
    end
            //更新out_channel
        end        
    end
    
    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            running <= 0;
        end else begin
            if (start_i && !running) begin
                running <= 1;
            end else if ((group_idx == GROUPS-1) && (out_channel == OUTPUT_DIM-1) && running) begin
                running <= 0;
                end
        end
    end           
    
    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            finish_r <= 1'b0;
        end else if (start_i && !running) begin
            finish_r <= 1'b0;
        end else if (running &&
                     (group_idx == GROUPS - 1) &&
                     (out_channel == OUTPUT_DIM - 1)) begin
            finish_r <= 1'b1;
        end
    end 

    // 延迟链 - 传递控制信号
    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            for (i = 0; i <= 14; i = i + 1) begin
                out_channel_dly[i] <= 0;
                group_idx_dly[i] <= 0;
            end
        end else begin
        out_channel_dly[0] <= out_channel;
        group_idx_dly[0]   <= group_idx;

        for (i = 1; i <= 14; i = i + 1) begin
            out_channel_dly[i] <= out_channel_dly[i-1];
            group_idx_dly[i]   <= group_idx_dly[i-1];
        end
            //根据流水线级数传递两个循环参数
        end
    end

    // 流水线阶段1: 地址生成 
    always @(posedge clk_i or negedge rst_n_i) begin 
        if (!rst_n_i) begin
            input_data_addr_o <= 0;  
            weight_addr_o <= 0;
            bias_addr_o <= 0;
        end else if (running) begin
        input_data_addr_o <= group_idx;
        weight_addr_o     <= {out_channel, 2'b00} + group_idx;
        bias_addr_o       <= out_channel;
            //计算输入数据、权重和偏置的地址
        end 
    end

    // 流水线阶段2-4: RAM读取数据输入乘法器
    assign mul_data1_o = input_data_i;
    assign mul_data2_o = weight_i;

    // 流水线阶段5-7: 乘法器运算 
      // 编写乘法运算代码


    // 流水线阶段8-10: 加法树 
    adder_tree adder (
        .clk(clk_i),
        .rst_n(rst_n_i),
        .data(mul_result_i),
        .sum_out(final_sum)
    );


    // 流水线阶段11: 通道累加(9级延迟)
    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            channel_accum <= 0;
        end else begin
        if (group_idx_dly[10] == 2'd0) begin
        channel_accum <= final_sum;
    end else begin
        channel_accum <=
            channel_accum + final_sum;
    end
            //if(对应的延迟循环变量的数值==？)
            //选择直接将final_sum赋值给channel_accum
            //or将channel_accum累加
        end
    end

    // 偏置延迟链
    reg [7:0] bias_reg [0:9];

    always @(posedge clk_i or negedge rst_n_i) begin
        if(!rst_n_i) begin
            for(i=0;i<=9;i=i+1)
                bias_reg[i] <= 8'd0;
        end
        else begin
        bias_reg[0] <= bias_i;
        for (i = 1; i <= 9; i = i + 1)
            bias_reg[i] <= bias_reg[i-1];
            //传递偏置数据
        end
    end    

    // 流水线阶段12: 添加偏置(10级延迟)
    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            accumulator <= 0;  
        end else begin
        if (group_idx_dly[11] == GROUPS - 1) begin
        accumulator <= channel_accum
                     + {{24{bias_reg[9][7]}}, bias_reg[9]};
    end
            //accumulator <= channel_accum[?] + {{24{bias_reg[?][7]}}, bias_reg[?]};
        end
    end

    //流水线阶段13: ReLU激活 
    reg [31:0] relu_result;

    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            relu_result <= 32'd0;
        end else begin
            if (accumulator[31]) begin
                relu_result <= 32'd0;
            end else begin
                relu_result <= accumulator;
            end
        end
    end

    always @(posedge clk_i or negedge rst_n_i) begin
        if (!rst_n_i) begin
            fc_output_wren_o <= 0;  
            fc_output_data_o <= 0;
            fc_output_addr_o <= 0;
        end else begin
        fc_output_wren_o <= (group_idx_dly[13] == GROUPS - 1);
        fc_output_data_o <= relu_result;
        fc_output_addr_o <= out_channel_dly[13];
            //定义fc_output_wren_o，fc_output_data_o，fc_output_addr_o
        end
    end

assign done_o = (group_idx_dly[13] == GROUPS - 1) &&
                (out_channel_dly[13] == OUTPUT_DIM - 1);
    //请自行定义done_o信号

endmodule