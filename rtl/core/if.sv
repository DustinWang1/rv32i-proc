module if (
    input logic clk,
    input logic rst,
    input logic pcSrc,
    input logic [31:0] jumpSrc,
    output logic [31:0] instrF,
    output logic [31:0] pcF,
    output logic [31:0] nextPcF,
);
logic pc, nextPc;

imem imem (clk, pc, instrF);

always_ff @(posedge clk) begin
    if(PCSrc == 1'b0) pc <= nextPc;
    else pc <= jumpSrc;
end

always_ff @(posedge clk) begin
    pcF <= pc;
    nextPcF <= nextPc;
end

endmodule