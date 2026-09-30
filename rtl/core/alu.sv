import rv32i_pkg::*;

module alu(
    input ALUControl_e ALUCon,
    input logic [31:0] ALUIn1,
    input logic [31:0] ALUIn2,
    output logic [31:0] ALUOut
);

logic [4:0] shamt;
assign shamt = ALUIn2[4:0];

always_comb begin
    case (ALUCon)
        ALU_ADD:  ALUOut = ALUIn1 + ALUIn2;
        ALU_SUB:  ALUOut = ALUIn1 - ALUIn2;
        ALU_AND:  ALUOut = ALUIn1 & ALUIn2;
        ALU_OR:   ALUOut = ALUIn1 | ALUIn2;
        ALU_XOR:  ALUOut = ALUIn1 ^ ALUIn2;
        ALU_SLL:  ALUOut = ALUIn1 << shamt;
        ALU_SRL:  ALUOut = ALUIn1 >> shamt;
        ALU_SRA:  ALUOut = $signed(ALUIn1) >>> shamt;
        ALU_SLT:  ALUOut = {31'b0, $signed(ALUIn1) < $signed(ALUIn2)};
        ALU_SLTU: ALUOut = {31'b0, ALUIn1 < ALUIn2};
        default:  ALUOut = 32'b0;
    endcase
end

endmodule