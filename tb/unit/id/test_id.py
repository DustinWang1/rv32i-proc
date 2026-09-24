import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Mirrors rv32i_pkg::imm_sel_e -- update if your enum's declared order differs
IMM_I, IMM_S, IMM_B, IMM_U, IMM_J = range(5)

OPCODES = {
    "LOAD": 0b0000011, "OP_IMM": 0b0010011, "STORE": 0b0100011,
    "OP": 0b0110011, "LUI": 0b0110111, "AUIPC": 0b0010111,
    "JAL": 0b1101111, "JALR": 0b1100111, "BRANCH": 0b1100011,
    "INVALID": 0b1111111,
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


def unpack_ctrl(dut):
    """ctrl_t = {imm_sel_e immSrc (3b); logic rf_we (1b)} packed MSB-first."""
    raw = dut.ctrlD.value.to_unsigned()
    rf_we = raw & 0x1
    imm_src = (raw >> 1) & 0x7
    return imm_src, rf_we


async def settle(dut):
    await Timer(1, unit="ns")  # let combinational logic propagate


async def reset_dut(dut):
    dut.rst.value = 1
    dut.rf_we.value = 0
    dut.a3.value = 0
    dut.w3.value = 0
    dut.instrF.value = 0
    dut.pcF.value = 0
    dut.nextPcF.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


@cocotb.test()
async def rf_x0_hardwired_zero(dut):
    """Writing to x0 must never be observable on either read port."""
    cocotb.start_soon(Clock(dut.clk, 3, unit="ns").start())
    await reset_dut(dut)

    dut.rf_we.value = 1
    dut.a3.value = 0
    dut.w3.value = 0xDEADBEEF
    dut.instrF.value = i_type(0, 0, 0, 0, OPCODES["OP_IMM"])  # rs1=x0
    await settle(dut)
    assert dut.rs1D.value.to_unsigned() == 0, "x0 forwarded write leaked through rs1D"

    await RisingEdge(dut.clk)
    dut.rf_we.value = 0
    await settle(dut)
    assert dut.rs1D.value.to_unsigned() == 0, "x0 write-protection broken after clock edge"


@cocotb.test()
async def rf_write_then_read_next_cycle(dut):
    """A write committed on cycle N must be visible via normal (non-forwarded) read on cycle N+1."""
    cocotb.start_soon(Clock(dut.clk, 3, unit="ns").start())
    await reset_dut(dut)

    dut.rf_we.value = 1
    dut.a3.value = 5
    dut.w3.value = 0x1234
    dut.instrF.value = i_type(0, 1, 0, 2, OPCODES["OP_IMM"])  # unrelated rs1/rd
    await RisingEdge(dut.clk)

    dut.rf_we.value = 0
    dut.instrF.value = i_type(0, 5, 0, 2, OPCODES["OP_IMM"])  # rs1 = x5
    await settle(dut)
    assert dut.rs1D.value.to_unsigned() == 0x1234, \
        f"expected retained write 0x1234, got {hex(dut.rs1D.value.to_unsigned())}"


@cocotb.test()
async def rf_raw_hazard_forwarding(dut):
    """Same-cycle write and read to the same address must forward combinationally (no RAW hazard)."""
    cocotb.start_soon(Clock(dut.clk, 3, unit="ns").start())
    await reset_dut(dut)

    # rs1 == rs2 == wa3, write and read collide in the same cycle
    dut.rf_we.value = 1
    dut.a3.value = 9
    dut.w3.value = 0xABCD1234
    dut.instrF.value = r_type(0, 9, 9, 0, 3, OPCODES["OP"])  # rs1=rs2=x9, rd=x3
    await settle(dut)

    assert dut.rs1D.value.to_unsigned() == 0xABCD1234, \
        f"RAW hazard: rs1D did not forward, got {hex(dut.rs1D.value.to_unsigned())}"
    assert dut.rs2D.value.to_unsigned() == 0xABCD1234, \
        f"RAW hazard: rs2D did not forward, got {hex(dut.rs2D.value.to_unsigned())}"

    # confirm the register array itself is only updated on the clock edge, not combinationally
    dut.rf_we.value = 0
    dut.instrF.value = r_type(0, 9, 9, 0, 3, OPCODES["OP"])
    await settle(dut)
    assert dut.rs1D.value.to_unsigned() == 0, \
        "write appears to have landed in the register array before the clock edge"

    await RisingEdge(dut.clk)
    await settle(dut)
    # rf_we was deasserted above, so nothing should have latched; register should remain 0
    assert dut.rs1D.value.to_unsigned() == 0


@cocotb.test()
async def decoder_field_extraction(dut):
    """rs1AddrD/rs2AddrD/rdD must mirror the instruction bit fields regardless of type."""
    cocotb.start_soon(Clock(dut.clk, 3, unit="ns").start())
    await reset_dut(dut)

    instr = r_type(0b0100000, 17, 22, 0, 11, OPCODES["OP"])
    dut.instrF.value = instr
    await settle(dut)

    assert dut.rs1AddrD.value.to_unsigned() == 22
    assert dut.rs2AddrD.value.to_unsigned() == 17
    assert dut.rdD.value.to_unsigned() == 11


@cocotb.test()
async def decoder_pc_passthrough(dut):
    """pcD/nextPcD are pure combinational passthroughs of pcF/nextPcF."""
    cocotb.start_soon(Clock(dut.clk, 3, unit="ns").start())
    await reset_dut(dut)

    dut.pcF.value = 0x1000
    dut.nextPcF.value = 0x1004
    await settle(dut)

    assert dut.pcD.value.to_unsigned() == 0x1000
    assert dut.nextPcD.value.to_unsigned() == 0x1004


@cocotb.test()
async def controller_opcode_decode(dut):
    """ctrlD.immSrc/rf_we must match the RV32I base-ISA opcode map."""
    cocotb.start_soon(Clock(dut.clk, 3, unit="ns").start())
    await reset_dut(dut)

    cases = [
        ("LOAD",    i_type(0, 1, 2, 5, OPCODES["LOAD"]),    IMM_I, 1),
        ("OP_IMM",  i_type(0, 1, 0, 5, OPCODES["OP_IMM"]),  IMM_I, 1),
        ("STORE",   s_type(0, 2, 1, 2, OPCODES["STORE"]),   IMM_S, 0),
        ("OP",      r_type(0, 2, 1, 0, 5, OPCODES["OP"]),   IMM_I, 1),
        ("LUI",     u_type(0xABCDE, 5, OPCODES["LUI"]),     IMM_U, 1),
        ("AUIPC",   u_type(0xABCDE, 5, OPCODES["AUIPC"]),   IMM_U, 1),
        ("JAL",     j_type(-256, 5, OPCODES["JAL"]),        IMM_J, 1),
        ("JALR",    i_type(4, 1, 0, 5, OPCODES["JALR"]),    IMM_I, 1),
        ("BRANCH",  b_type(-16, 2, 1, 0, OPCODES["BRANCH"]), IMM_B, 0),
        ("INVALID", i_type(0, 1, 0, 5, OPCODES["INVALID"]), IMM_I, 0),
    ]

    for name, instr, exp_imm_src, exp_rf_we in cases:
        dut.instrF.value = instr
        await settle(dut)
        imm_src, rf_we = unpack_ctrl(dut)
        assert imm_src == exp_imm_src, f"{name}: immSrc={imm_src}, expected {exp_imm_src}"
        assert rf_we == exp_rf_we, f"{name}: rf_we={rf_we}, expected {exp_rf_we}"


@cocotb.test()
async def imm_ext_all_types(dut):
    """immD must sign-extend (or place, for U-type) the immediate correctly for every instruction type."""
    cocotb.start_soon(Clock(dut.clk, 3, unit="ns").start())
    await reset_dut(dut)

    tests = [
        ("I-type: addi x5,x4,-5",
         i_type(-5, 4, 0, 5, OPCODES["OP_IMM"]), -5, False),
        ("I-type: addi x5,x4,2047 (max positive)",
         i_type(2047, 4, 0, 5, OPCODES["OP_IMM"]), 2047, False),
        ("I-type: jalr x1,x2,-2048 (min negative)",
         i_type(-2048, 2, 0, 1, OPCODES["JALR"]), -2048, False),
        ("S-type: sw x6,-8(x7)",
         s_type(-8, 6, 7, 0b010, OPCODES["STORE"]), -8, False),
        ("S-type: sb x6,2047(x7)",
         s_type(2047, 6, 7, 0b000, OPCODES["STORE"]), 2047, False),
        ("B-type: beq x9,x10,-16",
         b_type(-16, 10, 9, 0, OPCODES["BRANCH"]), -16, False),
        ("B-type: bne x9,x10,4094 (max even positive)",
         b_type(4094, 10, 9, 1, OPCODES["BRANCH"]), 4094, False),
        ("U-type: lui x8,0xABCDE",
         u_type(0xABCDE, 8, OPCODES["LUI"]), (0xABCDE << 12) & 0xFFFFFFFF, True),
        ("U-type: auipc x8,0xFFFFF",
         u_type(0xFFFFF, 8, OPCODES["AUIPC"]), (0xFFFFF << 12) & 0xFFFFFFFF, True),
        ("J-type: jal x11,-256",
         j_type(-256, 11, OPCODES["JAL"]), -256, False),
        ("J-type: jal x11,1048574 (max even positive)",
         j_type(1048574, 11, OPCODES["JAL"]), 1048574, False),
    ]

    for name, instr, imm_exp, imm_unsigned in tests:
        dut.instrF.value = instr
        await settle(dut)

        got_imm = dut.immD.value.to_unsigned() if imm_unsigned else dut.immD.value.to_signed()
        assert got_imm == imm_exp, f"{name}: immD={got_imm}, expected {imm_exp}"
