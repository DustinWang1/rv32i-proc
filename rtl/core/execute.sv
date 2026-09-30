import rv32i_pkg::*;

module execute(
    input logic [31:0] rs1D,
    input logic [31:0] rs2D,
    input logic [4:0] rs1AddrD,
    input logic [4:0] rs2AddrD,
    input logic [4:0] rdD,
    input logic [31:0] immD,
    input logic [31:0] pcD,
    input logic [31:0] nextPcD,
    input ctrl_t ctrlD,
    input logic [31:0] rs1MemForward,
    input logic [31:0] rs2MemForward,
    input logic [31:0] rs1WbForward,
    input logic [31:0] rs2WbForward,
    input forward_sel_e rs1_forward,
    input forward_sel_e rs2_forward,
    output ctrl_t ctrlE,
    output logic [31:0] ALUResE,
    output logic [31:0] WriteDataE,
    output logic [31:0] PCTargetE,
    output logic [4:0] rs1AddrE,
    output logic [4:0] rs2AddrE,
    output logic [4:0] rdE,
    output logic [31:0] nextPcE
);

assign rs1AddrE = rs1AddrD;
assign rs2AddrE = rs2AddrD;
assign rdE = rdD;
assign nextPcE = nextPcD;

assign PCTargetE = immD + pcD;

logic [31:0] ALUIn1;
logic [31:0] ALUIn2;
logic [31:0] rs2_forward_out;

assign WriteDataE = ALUIn2;

always_comb begin
    casez (rs2_forward)
        FORWARD_RS: 
            rs2_forward_out = rs2D;
        FORWARD_MEM:
            rs2_forward_out = rs2MemForward;
        FORWARD_WB:
            rs2_forward_out = rs2WbForward;
        default: 
            rs2_forward_out = '0;
    endcase
end

always_comb begin
    casez (ctrlD.ALUSrc)
        SRC_IMM:
            ALUIn2 = immD;
        SRC_RS2:
            ALUIn2 = rs2_forward_out;
        default:
            ALUIn2 = '0;
    endcase
end

always_comb begin
    casez (rs1_forward)
        FORWARD_RS: 
            ALUIn1 = rs1D;
        FORWARD_MEM:
            ALUIn1 = rs1MemForward;
        FORWARD_WB:
            ALUIn1 = rs1WbForward;
        default: 
            ALUIn1 = '0;
    endcase
end

alu alu(ctrlD.ALUCon, ALUIn1, ALUIn2, ALUResE);



endmodule
