module fetch # (
    parameter int ADDR_WIDTH = 8,
    parameter string INIT_FILE = ""
) (
    input logic clk,
    input logic rst,
    input logic stall,
    input logic flush,
    input logic pcSrc,
    input logic [31:0] jumpAddr,
    output logic [31:0] instrF,
    output logic [31:0] pcF,
    output logic [31:0] nextPcF
);
logic [31:0] prevPc, pc, nextPc;
logic [31:0] imemAddr;
logic [31:0] instr;
logic flush_flag;
logic rst_flag;

imem #(.ADDR_WIDTH(ADDR_WIDTH), .INIT_FILE(INIT_FILE)) imem(clk, imemAddr, instr);

assign instrF = rst || rst_flag || flush || flush_flag ? 32'h00000013 : instr;
assign nextPc = pc + 32'd4;
assign prevPc = pc - 32'd4;

assign imemAddr = stall ? {2'b0, prevPc[31:2]} : {2'b0, pc[31:2]};

always_ff @(posedge clk) begin
    if(rst) begin
        flush_flag <= 0;
    end else begin
        if(flush == 1'b1) flush_flag <= 1;
        else flush_flag <= 0;
    end
end

always_ff @(posedge clk) begin
    if(rst) begin
        rst_flag <= 1;
    end else begin
        rst_flag <= 0;
    end
end

always_ff @(posedge clk) begin
    if(rst) begin
        pc <= 0;
    end else begin
        if(stall == 1'b0) 
            if(pcSrc == 1'b0) pc <= nextPc;
            else pc <= jumpAddr;
    end
end

always_ff @(posedge clk) begin
    if(rst) begin
        pcF <= 0;
        nextPcF <= 0;
    end else begin
        if(stall == 1'b0) begin
            pcF <= pc;
            nextPcF <= nextPc;
        end
    end
end

endmodule