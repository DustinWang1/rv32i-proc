import rv32i_pkg::*;

module controller (
    input logic [31:0] instr,
    output ctrl_t ctrl
);

always_comb begin
    ctrl = '0;

    unique casez (instr[6:0])
        7'b0000011: begin // LOAD
            ctrl.immSrc = IMM_I;
            ctrl.rf_we  = 1'b1;
        end
        7'b0010011: begin // OP-IMM
            ctrl.immSrc = IMM_I;
            ctrl.rf_we  = 1'b1;
        end
        7'b0100011: begin // STORE
            ctrl.immSrc = IMM_S;
            ctrl.rf_we  = 1'b0;
        end
        7'b0110011: begin // OP
            ctrl.immSrc = IMM_I; // not used for R-type decode, but kept valid
            ctrl.rf_we  = 1'b1;
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
        end
        default: begin
            ctrl.immSrc = IMM_I;
            ctrl.rf_we  = 1'b0;
        end
    endcase
end

endmodule