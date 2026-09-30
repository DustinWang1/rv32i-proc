package rv32i_pkg;
    typedef enum logic [2:0] {  
        IMM_I,
        IMM_S,
        IMM_B,
        IMM_U,
        IMM_J
    } imm_sel_e;

    typedef enum logic [1:0] {
        FORWARD_RS,
        FORWARD_MEM,
        FORWARD_WB
    } forward_sel_e;

    typedef enum logic {
        SRC_IMM,
        SRC_RS2
    } ALUSrc_e;

    typedef enum logic [3:0] {
        ALU_ADD,
        ALU_SUB,
        ALU_AND,
        ALU_OR,
        ALU_XOR,
        ALU_SLL,
        ALU_SRL,
        ALU_SRA,
        ALU_SLT,
        ALU_SLTU
    } ALUControl_e;

    typedef struct packed {
      ALUSrc_e ALUSrc;
      ALUControl_e ALUCon;
      imm_sel_e immSrc;
      logic rf_we;
    } ctrl_t;

endpackage