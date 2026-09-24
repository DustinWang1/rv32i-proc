package rv32i_pkg;
    typedef enum logic [2:0] {  
        IMM_I,
        IMM_S,
        IMM_B,
        IMM_U,
        IMM_J
    } imm_sel_e;

    typedef struct packed {
      imm_sel_e immSrc;
      logic rf_we;
    } ctrl_t;

endpackage