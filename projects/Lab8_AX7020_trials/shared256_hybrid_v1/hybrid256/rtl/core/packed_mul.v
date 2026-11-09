`timescale 1ns/1ps
// LUT6_2 generate/add, exact signed radix4 partial product; M+2-bit modular accumulator.
module packed_ga #(parameter M=24)(input wire [M-1:0] a,input wire [2:0] digit,input wire [M+1:0] acc,output wire [M+1:0] sum);
 localparam N=M+2,C=((N+3)/4)*4;
 wire [C-1:0] pr,ge,co,oo;
 generate for(genvar i=0;i<M+1;i=i+1)begin:g
  wire xi=(i<M)?a[i]:a[M-1];
  wire xm=(i==0)?1'b0:((i<=M)?a[i-1]:a[M-1]);
  LUT6_2 #(.INIT(64'h0aac355ff553caa0)) u(.I0(xi),.I1(xm),.I2(digit[0]),.I3(digit[1]),.I4(digit[2]),.I5(acc[i]),.O5(ge[i]),.O6(pr[i]));
 end
 endgenerate
 // Arithmetic-shifted accumulator top2 bits and multiplicand sign extension coincide.
 assign pr[M+1]=pr[M];assign ge[M+1]=ge[M];
 generate if(C>N)begin assign pr[C-1:N]=0;assign ge[C-1:N]=0;end
 for(genvar j=0;j<C/4;j=j+1)begin:c
  CARRY4 u(.CI(j==0?1'b0:co[j*4-1]),.CYINIT(j==0?digit[2]:1'b0),.DI(ge[j*4+:4]),.S(pr[j*4+:4]),.CO(co[j*4+:4]),.O(oo[j*4+:4]));
 end endgenerate
 assign sum=oo[N-1:0];
endmodule
module packed_mul #(parameter METHOD=0)(input wire clk_i,ce_i,input wire signed [24:0] b,input wire signed [7:0] x,output wire [15:0] y0,y1);
 generate if(METHOD==0)begin:generic25
  (* use_dsp="no" *) reg signed [32:0] p;
  reg signed [32:0] q,r;
  always @(posedge clk_i)if(ce_i)begin p<=b*x;q<=p;r<=q;end
  assign y0=r[15:0];assign y1=$signed(r[32:16])+r[15];
 end else if(METHOD==1)begin:booth24
  wire [25:0] z0,z1,z2,z3;reg [25:0] z1d;reg [1:0] low;reg [23:0] ad;reg [4:0] xd;reg [31:0] result,delayed;
  packed_ga #(.M(24)) s0(b[23:0],{x[1:0],1'b0},26'd0,z0);
  packed_ga #(.M(24)) s1(b[23:0],x[3:1],{{2{z0[25]}},z0[25:2]},z1);
  packed_ga #(.M(24)) s2(ad,xd[2:0],{{2{z1d[25]}},z1d[25:2]},z2);
  packed_ga #(.M(24)) s3(ad,xd[4:2],{{2{z2[25]}},z2[25:2]},z3);
  always @(posedge clk_i)if(ce_i)begin ad<=b[23:0];xd<=x[7:3];z1d<=z1;low<=z0[1:0];result<={z3,z2[1:0],z1d[1:0],low};delayed<=result;end
  assign y0=delayed[15:0];assign y1=$signed(delayed[31:16])+delayed[15];
 end else begin:packed_sparse
  // Recode packed B, discard exactly-zero digits4..7. Keep the cross-band Booth bit B15.
  // This is a sparse 24x8 packed multiplication, not two decoded ordinary coefficients.
  reg [7:0] xd;
  always @(posedge clk_i)if(ce_i)xd<=x;
  for(genvar h=0;h<2;h=h+1)begin:band
   wire [7:0] w=h==0?b[7:0]:b[23:16];
   wire previous=h==0?1'b0:b[15];
   wire [9:0] z0,z1,z2,z3;reg [9:0] z1d;reg [1:0] low;reg [4:0] wd;reg [15:0] result,delayed;
   packed_ga #(.M(8)) s0(x,{w[1:0],previous},10'd0,z0);
   packed_ga #(.M(8)) s1(x,w[3:1],{{2{z0[9]}},z0[9:2]},z1);
   packed_ga #(.M(8)) s2(xd,wd[2:0],{{2{z1d[9]}},z1d[9:2]},z2);
   packed_ga #(.M(8)) s3(xd,wd[4:2],{{2{z2[9]}},z2[9:2]},z3);
   always @(posedge clk_i)if(ce_i)begin z1d<=z1;low<=z0[1:0];wd<=w[7:3];result<={z3,z2[1:0],z1d[1:0],low};delayed<=result;end
   if(h==0)assign y0=delayed;else assign y1=delayed;
  end
 end endgenerate
endmodule
