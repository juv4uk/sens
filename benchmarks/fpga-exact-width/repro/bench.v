module decoder3(input clk,input [2:0] code,output reg [7:0] onehot,output reg valid);
always @(posedge clk) begin valid<=1'b1; onehot<=8'b1<<code; end endmodule
module decoder4(input clk,input [3:0] code,output reg [7:0] onehot,output reg valid);
always @(posedge clk) begin valid<=~code[3]; onehot<=code[3]?8'b0:(8'b1<<code[2:0]); end endmodule
module decoder8(input clk,input [7:0] code,output reg [7:0] onehot,output reg valid);
always @(posedge clk) begin valid<=~|code[7:3]; onehot<=(|code[7:3])?8'b0:(8'b1<<code[2:0]); end endmodule

module alu #(parameter W=3)(input clk,input [W-1:0] a,input [W-1:0] b,input sel,output reg [W:0] y);
always @(posedge clk) begin
  if(sel) y<={1'b0,(a^b)};
  else y<={1'b0,a}+{1'b0,b};
end endmodule
module alu3(input clk,input [2:0] a,b,input sel,output [3:0] y); alu #(.W(3)) u(clk,a,b,sel,y); endmodule
module alu4(input clk,input [3:0] a,b,input sel,output [4:0] y); alu #(.W(4)) u(clk,a,b,sel,y); endmodule
module alu8(input clk,input [7:0] a,b,input sel,output [8:0] y); alu #(.W(8)) u(clk,a,b,sel,y); endmodule

module ram #(parameter W=3)(input clk,input we,input [9:0] addr,input [W-1:0] wdata,output reg [W-1:0] rdata);
reg [W-1:0] mem [0:1023];
always @(posedge clk) begin
  if(we) mem[addr]<=wdata;
  else rdata<=mem[addr];
end endmodule
module ram3(input clk,we,input [9:0] addr,input [2:0] wdata,output [2:0] rdata); ram #(.W(3)) u(clk,we,addr,wdata,rdata); endmodule
module ram4(input clk,we,input [9:0] addr,input [3:0] wdata,output [3:0] rdata); ram #(.W(4)) u(clk,we,addr,wdata,rdata); endmodule
module ram8(input clk,we,input [9:0] addr,input [7:0] wdata,output [7:0] rdata); ram #(.W(8)) u(clk,we,addr,wdata,rdata); endmodule
