import rv32i_pkg::*;

module decoder(
    input logic clk, rst, rf_we,
    input logic [31:0] instrF,
    input logic [31:0] pcF,
    input logic [31:0] nextPcF,
    input logic [4:0] a3,
    input logic [31:0] w3,
    output logic [31:0] rs1D,
    output logic [31:0] rs2D,
    output logic [4:0] rs1AddrD,
    output logic [4:0] rs2AddrD,
    output logic [4:0] rdD,
    output logic [31:0] immD,
    output logic [31:0] pcD,
    output logic [31:0] nextPcD,
    output ctrl_t ctrlD
);

controller controller(instrF, ctrlD);

rf rf(clk, rst, rf_we, instrF[19:15], instrF[24:20], a3, w3, rs1D, rs2D);

ext ext(ctrlD.immSrc, instrF[31:7], immD);

assign rs1AddrD = instrF[19:15];
assign rs2AddrD = instrF[24:20];
assign rdD = instrF[11:7];
assign pcD = pcF;
assign nextPcD = nextPcF;

endmodule