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
     r1 = registers[a1];
     r2 = registers[a2];
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