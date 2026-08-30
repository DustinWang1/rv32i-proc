
module imem #(
    parameter int ADDR_WIDTH = 8,
    parameter string INIT_FILE = ""
) (
    input logic clk,
    input logic [31:0] address,
    output logic [31:0] instr
);
    logic [31:0] mem[2**ADDR_WIDTH-1:0];

    // Test Instruction Memory
    initial begin
        $readmemh(INIT_FILE, mem, 0, 2**ADDR_WIDTH-1);
    end

    always_ff @(posedge clk) begin
        instr <= mem[address];
    end

endmodule