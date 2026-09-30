import random

import cocotb
from cocotb.triggers import Timer

# Mirrors rv32i_pkg::ALUControl_e -- update if your enum's declared order differs
(ALU_ADD, ALU_SUB, ALU_AND, ALU_OR, ALU_XOR,
 ALU_SLL, ALU_SRL, ALU_SRA, ALU_SLT, ALU_SLTU) = range(10)

MASK32 = 0xFFFFFFFF


def to_u32(v):
    return v & MASK32


def to_s32(v):
    v &= MASK32
    return v - (1 << 32) if v & 0x8000_0000 else v


def model(op, a, b):
    """Reference model matching the RTL's always_comb case."""
    shamt = b & 0x1F
    if op == ALU_ADD:
        return to_u32(a + b)
    if op == ALU_SUB:
        return to_u32(a - b)
    if op == ALU_AND:
        return a & b
    if op == ALU_OR:
        return a | b
    if op == ALU_XOR:
        return a ^ b
    if op == ALU_SLL:
        return to_u32(a << shamt)
    if op == ALU_SRL:
        return a >> shamt
    if op == ALU_SRA:
        return to_u32(to_s32(a) >> shamt)
    if op == ALU_SLT:
        return 1 if to_s32(a) < to_s32(b) else 0
    if op == ALU_SLTU:
        return 1 if a < b else 0
    raise ValueError(op)


OP_NAMES = {
    ALU_ADD: "ADD", ALU_SUB: "SUB", ALU_AND: "AND", ALU_OR: "OR",
    ALU_XOR: "XOR", ALU_SLL: "SLL", ALU_SRL: "SRL", ALU_SRA: "SRA",
    ALU_SLT: "SLT", ALU_SLTU: "SLTU",
}


async def check(dut, op, a, b):
    dut.ALUCon.value = op
    dut.ALUIn1.value = a
    dut.ALUIn2.value = b
    await Timer(1, unit="ns")
    expected = model(op, a, b)
    got = dut.ALUOut.value.to_unsigned()
    assert got == expected, (
        f"{OP_NAMES[op]}: a={hex(a)} b={hex(b)} -> got {hex(got)}, expected {hex(expected)}"
    )


DIRECTED_VALUES = [
    0x0000_0000, 0x0000_0001, 0xFFFF_FFFF, 0x8000_0000, 0x7FFF_FFFF,
    0x0000_0002, 0xAAAA_AAAA, 0x5555_5555, 0x0000_001F, 0x0000_0020,
]


@cocotb.test()
async def alu_add(dut):
    """ADD wraps around on overflow (two's complement, no carry-out signal)."""
    cases = [(1, 1, 2), (0xFFFFFFFF, 1, 0), (0x7FFFFFFF, 1, 0x80000000), (0, 0, 0)]
    for a, b, _ in cases:
        await check(dut, ALU_ADD, a, b)
    for a in DIRECTED_VALUES:
        for b in DIRECTED_VALUES:
            await check(dut, ALU_ADD, a, b)


@cocotb.test()
async def alu_sub(dut):
    """SUB wraps around on underflow."""
    cases = [(1, 1), (0, 1), (0x80000000, 1), (5, 3)]
    for a, b in cases:
        await check(dut, ALU_SUB, a, b)
    for a in DIRECTED_VALUES:
        for b in DIRECTED_VALUES:
            await check(dut, ALU_SUB, a, b)


@cocotb.test()
async def alu_bitwise(dut):
    """AND / OR / XOR are bitwise and symmetric."""
    for op in (ALU_AND, ALU_OR, ALU_XOR):
        for a in DIRECTED_VALUES:
            for b in DIRECTED_VALUES:
                await check(dut, op, a, b)


@cocotb.test()
async def alu_shifts(dut):
    """SLL/SRL/SRA only use the low 5 bits of ALUIn2 as shift amount."""
    values = [0x8000_0001, 0xFFFF_FFFF, 0x0000_0001, 0x7FFF_FFFF, 0x1234_5678]
    for a in values:
        for shamt in range(32):
            b = shamt  # low 5 bits equal shamt directly
            await check(dut, ALU_SLL, a, b)
            await check(dut, ALU_SRL, a, b)
            await check(dut, ALU_SRA, a, b)

    # upper bits of ALUIn2 beyond [4:0] must be ignored for shift amount
    await check(dut, ALU_SLL, 0x1, 0xFFFF_FFE1)  # shamt = 1
    await check(dut, ALU_SRL, 0x8000_0000, 0xFFFF_FFE1)
    await check(dut, ALU_SRA, 0x8000_0000, 0xFFFF_FFE1)


@cocotb.test()
async def alu_slt(dut):
    """SLT is signed comparison."""
    cases = [
        (1, 2), (2, 1), (0xFFFFFFFF, 1),  # -1 < 1
        (1, 0xFFFFFFFF),                  # 1 < -1 is false
        (0x80000000, 0x7FFFFFFF),         # INT_MIN < INT_MAX
        (0x7FFFFFFF, 0x80000000),         # INT_MAX < INT_MIN is false
        (5, 5),
    ]
    for a, b in cases:
        await check(dut, ALU_SLT, a, b)


@cocotb.test()
async def alu_sltu(dut):
    """SLTU is unsigned comparison."""
    cases = [
        (1, 2), (2, 1), (0xFFFFFFFF, 1), (1, 0xFFFFFFFF),
        (0x80000000, 0x7FFFFFFF), (0x7FFFFFFF, 0x80000000), (5, 5),
        (0, 0), (0, 1),
    ]
    for a, b in cases:
        await check(dut, ALU_SLTU, a, b)


@cocotb.test()
async def alu_is_purely_combinational(dut):
    """Output must update within the same timestep without any clock edge."""
    dut.ALUCon.value = ALU_ADD
    dut.ALUIn1.value = 1
    dut.ALUIn2.value = 1
    await Timer(1, unit="ns")
    assert dut.ALUOut.value.to_unsigned() == 2

    # Change inputs and re-check without toggling any clock
    dut.ALUIn1.value = 41
    dut.ALUIn2.value = 1
    await Timer(1, unit="ns")
    assert dut.ALUOut.value.to_unsigned() == 42

    dut.ALUCon.value = ALU_SUB
    await Timer(1, unit="ns")
    assert dut.ALUOut.value.to_unsigned() == 40


@cocotb.test()
async def alu_randomized(dut):
    """Randomized cross-check against the reference model for every opcode."""
    random.seed(0xA1CE0)
    ops = [ALU_ADD, ALU_SUB, ALU_AND, ALU_OR, ALU_XOR,
           ALU_SLL, ALU_SRL, ALU_SRA, ALU_SLT, ALU_SLTU]
    for _ in range(500):
        op = random.choice(ops)
        a = random.randint(0, MASK32)
        b = random.randint(0, MASK32)
        await check(dut, op, a, b)
