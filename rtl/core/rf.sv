module rf (
    input logic clk, rst, we,
    input logic [4:0] a1,
    input logic [4:0] a2,
    input logic [4:0] wa3,
    input logic [31:0] wd,
    output logic [31:0] r1,
    output logic [31:0] r2
);

logic [31:0] registers [31:0];

always_comb begin
    if (a1 == 5'd0)               r1 = 32'b0;           // x0 is always zero
    else if (we && a1 == wa3)     r1 = wd;              // being written this cycle, pass it through
    else                          r1 = registers[a1];

    if (a2 == 5'd0)               r2 = 32'b0;
    else if (we && a2 == wa3)     r2 = wd;
    else                          r2 = registers[a2];
end

always_ff @(posedge clk) begin
    if(rst) begin
        registers <= '{default: 32'b0};
    end else begin
        if(wa3 != 0 && we == 1) begin
            registers[wa3] <= wd;
        end
    end
end

endmodule