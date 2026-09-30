import rv32i_pkg::*;

module controller (
    input logic [31:0] instr,
    output ctrl_t ctrl
);

always_comb begin
    ctrl = '0;
    ctrl.ALUSrc = SRC_IMM;
    ctrl.ALUCon = ALU_ADD;

    unique casez (instr[6:0])
        7'b0000011: begin // LOAD
            ctrl.immSrc = IMM_I;
            ctrl.rf_we  = 1'b1;
            ctrl.ALUCon = ALU_ADD;
        end
        7'b0010011: begin // OP-IMM
            ctrl.immSrc = IMM_I;
            ctrl.rf_we  = 1'b1;
            case (instr[14:12])
                3'b000: ctrl.ALUCon = ALU_ADD;
                3'b001: ctrl.ALUCon = ALU_SLL;
                3'b010: ctrl.ALUCon = ALU_SLT;
                3'b011: ctrl.ALUCon = ALU_SLTU;
                3'b100: ctrl.ALUCon = ALU_XOR;
                3'b101: ctrl.ALUCon = (instr[31:25] == 7'b0100000) ? ALU_SRA : ALU_SRL;
                3'b110: ctrl.ALUCon = ALU_OR;
                3'b111: ctrl.ALUCon = ALU_AND;
                default: ctrl.ALUCon = ALU_ADD;
            endcase
        end
        7'b0100011: begin // STORE
            ctrl.immSrc = IMM_S;
            ctrl.rf_we  = 1'b0;
            ctrl.ALUCon = ALU_ADD;
        end
        7'b0110011: begin // OP
            ctrl.immSrc = IMM_I; // not used for R-type decode, but kept valid
            ctrl.rf_we  = 1'b1;
            ctrl.ALUSrc = SRC_RS2;
            case (instr[14:12])
                3'b000: ctrl.ALUCon = (instr[31:25] == 7'b0100000) ? ALU_SUB : ALU_ADD;
                3'b001: ctrl.ALUCon = ALU_SLL;
                3'b010: ctrl.ALUCon = ALU_SLT;
                3'b011: ctrl.ALUCon = ALU_SLTU;
                3'b100: ctrl.ALUCon = ALU_XOR;
                3'b101: ctrl.ALUCon = (instr[31:25] == 7'b0100000) ? ALU_SRA : ALU_SRL;
                3'b110: ctrl.ALUCon = ALU_OR;
                3'b111: ctrl.ALUCon = ALU_AND;
                default: ctrl.ALUCon = ALU_ADD;
            endcase
        end
        7'b0110111: begin // LUI
            ctrl.immSrc = IMM_U;
            ctrl.rf_we  = 1'b1;
        end
        7'b0010111: begin // AUIPC
            ctrl.immSrc = IMM_U;
            ctrl.rf_we  = 1'b1;
        end
        7'b1101111: begin // JAL
            ctrl.immSrc = IMM_J;
            ctrl.rf_we  = 1'b1;
        end
        7'b1100111: begin // JALR
            ctrl.immSrc = IMM_I;
            ctrl.rf_we  = 1'b1;
        end
        7'b1100011: begin // BRANCH
            ctrl.immSrc = IMM_B;
            ctrl.rf_we  = 1'b0;
            ctrl.ALUSrc = SRC_RS2;
            case (instr[14:12])
                3'b000, 3'b001: ctrl.ALUCon = ALU_SUB;
                3'b100, 3'b101: ctrl.ALUCon = ALU_SLT;
                3'b110, 3'b111: ctrl.ALUCon = ALU_SLTU;
                default: ctrl.ALUCon = ALU_SUB;
            endcase
        end
        default: begin
            ctrl.immSrc = IMM_I;
            ctrl.rf_we  = 1'b0;
        end
    endcase
end

endmodule