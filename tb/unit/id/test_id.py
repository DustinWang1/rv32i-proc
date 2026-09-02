import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Mirrors rv32i_pkg::imm_sel_e -- update if your enum's declared order differs
IMM_I, IMM_S, IMM_B, IMM_U, IMM_J, IMM_NONE = range(6)

OPCODES = {
    "R": 0b0110011, "I": 0b0010011, "S": 0b0100011,
    "B": 0b1100011, "U": 0b0110111, "J": 0b1101111,
}

def r_type(funct7, rs2, rs1, funct3, rd, opcode):
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

def i_type(imm, rs1, funct3, rd, opcode):
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

def s_type(imm, rs2, rs1, funct3, opcode):
    imm &= 0xFFF
    return (((imm >> 5) & 0x7F) << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | ((imm & 0x1F) << 7) | opcode

def b_type(imm, rs2, rs1, funct3, opcode):
    imm &= 0x1FFF
    return (((imm >> 12) & 0x1) << 31) | (((imm >> 5) & 0x3F) << 25) | (rs2 << 20) | (rs1 << 15) \
         | (funct3 << 12) | (((imm >> 1) & 0xF) << 8) | (((imm >> 11) & 0x1) << 7) | opcode

def u_type(imm20, rd, opcode):
    return ((imm20 & 0xFFFFF) << 12) | (rd << 7) | opcode

def j_type(imm, rd, opcode):
    imm &= 0x1FFFFF
    return (((imm >> 20) & 0x1) << 31) | (((imm >> 1) & 0x3FF) << 21) | (((imm >> 11) & 0x1) << 20) \
         | (((imm >> 12) & 0xFF) << 12) | (rd << 7) | opcode


async def settle(dut):
    await Timer(1, unit="ns")   # let combinational logic propagate, no clock edge needed


async def reset_dut(dut):
    dut.rst.value = 1
    dut.rf_we.value = 0
    dut.rdW.value = 0
    dut.wdW.value = 0
    dut.instrF.value = 0
    dut.immSrc.value = IMM_NONE
    dut.pcF.value = 0
    dut.nextPcF.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


async def fill_regfile(dut):
    """RF[n] <= n for x1..x31 (x0 left untouched -- it's hardwired anyway)."""
    dut.rf_we.value = 1
    for n in range(1, 32):
        dut.rdW.value = n
        dut.wdW.value = n
        await RisingEdge(dut.clk)
    dut.rf_we.value = 0
    await settle(dut)


@cocotb.test()
async def rf_test(dut):
    cocotb.start_soon(Clock(dut.clk, 3, unit="ns").start())

    await reset_dut(dut)
    await fill_regfile(dut)

    # Try to sneak a write into x0 -- confirm it's discarded before trusting anything else
    dut.rf_we.value = 1
    dut.rdW.value = 0
    dut.wdW.value = 0xDEADBEEF
    await RisingEdge(dut.clk)
    dut.rf_we.value = 0
    await settle(dut)

    dut.instrF.value = 0     # every field is 0, so rs1 addr = x0
    dut.immSrc.value = IMM_NONE
    await settle(dut)
    assert dut.rs1D.value.to_unsigned() == 0, \
        f"x0 write-protection broken: rs1D={dut.rs1D.value.to_unsigned()}"
    dut._log.info("PASS  x0 write-protection")

    tests = [
        # name, instr, immSrc, expected imm (signed unless noted), unsigned?
        ("R-type: add x3,x1,x2",
         r_type(0, 2, 1, 0, 3, OPCODES["R"]), IMM_NONE, 0, False),
        ("I-type: addi x5,x4,-5",
         i_type(-5, 4, 0, 5, OPCODES["I"]), IMM_I, -5, False),
        ("S-type: sw x6,-8(x7)",
         s_type(-8, 6, 7, 0b010, OPCODES["S"]), IMM_S, -8, False),
        ("U-type: lui x8,0xABCDE",
         u_type(0xABCDE, 8, OPCODES["U"]), IMM_U, (0xABCDE << 12) & 0xFFFFFFFF, True),
        ("B-type: beq x9,x10,-16",
         b_type(-16, 10, 9, 0, OPCODES["B"]), IMM_B, -16, False),
        ("J-type: jal x11,-256",
         j_type(-256, 11, OPCODES["J"]), IMM_J, -256, False),
    ]

    for name, instr, imm_sel, imm_exp, imm_unsigned in tests:
        dut.instrF.value = instr
        dut.immSrc.value = imm_sel
        await settle(dut)

        exp_rs1 = (instr >> 15) & 0x1F
        exp_rs2 = (instr >> 20) & 0x1F
        exp_rd  = (instr >> 7)  & 0x1F

        assert dut.rs1AddrD.value.to_unsigned() == exp_rs1, f"{name}: rs1AddrD wrong"
        assert dut.rs2AddrD.value.to_unsigned() == exp_rs2, f"{name}: rs2AddrD wrong"
        assert dut.rdD.value.to_unsigned() == exp_rd, f"{name}: rdD wrong"

        got_rs1 = dut.rs1D.value.to_unsigned()
        got_rs2 = dut.rs2D.value.to_unsigned()
        assert got_rs1 == exp_rs1, f"{name}: rs1D={got_rs1}, expected {exp_rs1}"
        assert got_rs2 == exp_rs2, f"{name}: rs2D={got_rs2}, expected {exp_rs2}"

        got_imm = dut.immD.value.to_unsigned() if imm_unsigned else dut.immD.value.to_signed()
        assert got_imm == imm_exp, f"{name}: immD={got_imm}, expected {imm_exp}"

        dut._log.info(f"PASS  {name}")
