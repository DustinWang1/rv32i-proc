import rv32i_pkg::*;

module ext (
    input imm_sel_e immSrc,
    input logic [31:7] instrIn,
    output logic [31:0] immOut
);

always_comb begin
    case(immSrc) 
        IMM_I: immOut = {{20{instrIn[31]}}, instrIn[31:20]}; //I type
        IMM_S: immOut = {{20{instrIn[31]}}, instrIn[31:25], instrIn[11:7]}; //S type
        IMM_B: immOut = {{20{instrIn[31]}}, instrIn[7], instrIn[30:25], instrIn[11:8], 1'b0}; //B type
        IMM_U: immOut = {instrIn[31], instrIn[30:20], instrIn[19:12], {12'b0}}; //U type
        IMM_J: immOut = {{12{instrIn[31]}}, instrIn[19:12], instrIn[20], instrIn[30:25], instrIn[24:21], 1'b0}; //J type
        default:
            immOut = 0;
    endcase
end

endmodule