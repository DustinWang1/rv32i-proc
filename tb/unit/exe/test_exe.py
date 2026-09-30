import cocotb
from cocotb.triggers import Timer

MASK32 = 0xFFFFFFFF

SRC_IMM, SRC_RS2 = range(2)
ALU_ADD, ALU_SUB, ALU_AND, ALU_OR, ALU_XOR, ALU_SLL, ALU_SRL, ALU_SRA, ALU_SLT, ALU_SLTU = range(10)

FORWARD_RS, FORWARD_MEM, FORWARD_WB = range(3)


def pack_ctrl(alu_src, alu_con):
	return (alu_src << 8) | (alu_con << 4)


def signed32(value):
	value &= MASK32
	return value - (1 << 32) if value & (1 << 31) else value


def expected_alu(alu_con, left, right):
	shift = right & 0x1F
	if alu_con == ALU_ADD:
		result = left + right
	elif alu_con == ALU_SUB:
		result = left - right
	elif alu_con == ALU_AND:
		result = left & right
	elif alu_con == ALU_OR:
		result = left | right
	elif alu_con == ALU_XOR:
		result = left ^ right
	elif alu_con == ALU_SLL:
		result = left << shift
	elif alu_con == ALU_SRL:
		result = left >> shift
	elif alu_con == ALU_SRA:
		result = signed32(left) >> shift
	elif alu_con == ALU_SLT:
		result = int(signed32(left) < signed32(right))
	elif alu_con == ALU_SLTU:
		result = int(left < right)
	else:
		raise AssertionError(f"unsupported ALU control {alu_con}")
	return result & MASK32


def drive_inputs(
	dut,
	*,
	rs1=0,
	rs2=0,
	rs1_addr=0,
	rs2_addr=0,
	rd=0,
	immediate=0,
	pc=0,
	next_pc=0,
	alu_src=SRC_IMM,
	alu_con=ALU_ADD,
	rs1_mem=0,
	rs2_mem=0,
	rs1_wb=0,
	rs2_wb=0,
	rs1_forward=FORWARD_RS,
	rs2_forward=FORWARD_RS,
):
	dut.rs1D.value = rs1
	dut.rs2D.value = rs2
	dut.rs1AddrD.value = rs1_addr
	dut.rs2AddrD.value = rs2_addr
	dut.rdD.value = rd
	dut.immD.value = immediate
	dut.pcD.value = pc
	dut.nextPcD.value = next_pc
	dut.ctrlD.value = pack_ctrl(alu_src, alu_con)
	dut.rs1MemForward.value = rs1_mem
	dut.rs2MemForward.value = rs2_mem
	dut.rs1WbForward.value = rs1_wb
	dut.rs2WbForward.value = rs2_wb
	dut.rs1_forward.value = rs1_forward
	dut.rs2_forward.value = rs2_forward


async def settle():
	await Timer(1, unit="ns")


@cocotb.test()
async def alu_operations(dut):
	"""Exercise every ALU control with signed, unsigned, and wraparound cases."""
	operations = [
		(ALU_ADD, "ADD"),
		(ALU_SUB, "SUB"),
		(ALU_AND, "AND"),
		(ALU_OR, "OR"),
		(ALU_XOR, "XOR"),
		(ALU_SLL, "SLL"),
		(ALU_SRL, "SRL"),
		(ALU_SRA, "SRA"),
		(ALU_SLT, "SLT"),
		(ALU_SLTU, "SLTU"),
	]

	for alu_con, name in operations:
		left = 0xFFFFFFFF
		right = 1
		drive_inputs(
			dut,
			rs1=left,
			rs2=right,
			alu_src=SRC_RS2,
			alu_con=alu_con,
		)
		await settle()
		expected = expected_alu(alu_con, left, right)
		actual = dut.ALUResE.value.to_unsigned()
		assert actual == expected, f"{name}: got {actual:#010x}, expected {expected:#010x}"


@cocotb.test()
async def forwarding_and_operand_selection(dut):
	"""Check each forwarding source and ensure immediate mode bypasses rs2 forwarding."""
	rs1_values = {
		FORWARD_RS: 0x10,
		FORWARD_MEM: 0x20,
		FORWARD_WB: 0x30,
	}
	rs2_values = {
		FORWARD_RS: 0x100,
		FORWARD_MEM: 0x200,
		FORWARD_WB: 0x300,
	}

	for rs1_forward, left in rs1_values.items():
		for rs2_forward, right in rs2_values.items():
			drive_inputs(
				dut,
				rs1=rs1_values[FORWARD_RS],
				rs2=rs2_values[FORWARD_RS],
				rs1_mem=rs1_values[FORWARD_MEM],
				rs1_wb=rs1_values[FORWARD_WB],
				rs2_mem=rs2_values[FORWARD_MEM],
				rs2_wb=rs2_values[FORWARD_WB],
				rs1_forward=rs1_forward,
				rs2_forward=rs2_forward,
				alu_src=SRC_RS2,
				alu_con=ALU_ADD,
			)
			await settle()
			assert dut.WriteDataE.value.to_unsigned() == right
			assert dut.ALUResE.value.to_unsigned() == left + right

	for rs1_forward, left in rs1_values.items():
		for rs2_forward in rs2_values:
			immediate = 0x456
			drive_inputs(
				dut,
				rs1=rs1_values[FORWARD_RS],
				rs1_mem=rs1_values[FORWARD_MEM],
				rs1_wb=rs1_values[FORWARD_WB],
				rs2=rs2_values[FORWARD_RS],
				rs2_mem=rs2_values[FORWARD_MEM],
				rs2_wb=rs2_values[FORWARD_WB],
				immediate=immediate,
				rs1_forward=rs1_forward,
				rs2_forward=rs2_forward,
				alu_src=SRC_IMM,
				alu_con=ALU_ADD,
			)
			await settle()
			assert dut.WriteDataE.value.to_unsigned() == immediate
			assert dut.ALUResE.value.to_unsigned() == left + immediate


@cocotb.test()
async def address_and_pc_passthroughs(dut):
	"""Verify register-address/next-PC passthroughs and 32-bit PC-target addition."""
	drive_inputs(
		dut,
		rs1_addr=5,
		rs2_addr=17,
		rd=23,
		pc=0xFFFFFFF0,
		immediate=0x30,
		next_pc=0x12345678,
	)
	await settle()

	assert dut.rs1AddrE.value.to_unsigned() == 5
	assert dut.rs2AddrE.value.to_unsigned() == 17
	assert dut.rdE.value.to_unsigned() == 23
	assert dut.nextPcE.value.to_unsigned() == 0x12345678
	assert dut.PCTargetE.value.to_unsigned() == 0x20

