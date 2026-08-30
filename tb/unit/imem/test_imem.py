import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def imem_test(dut):
    Clock(dut.clk, 1, unit="ns").start()

    await Timer(1, 'ns')

    depth = 2**int(dut.ADDR_WIDTH.value)
    cocotb.log.info(dut.mem[4])
    for addr in range(depth):
        dut.address.value = addr
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        assert int(dut.instr.value) == addr, f"addr {addr}: expected {addr}, got {int(dut.instr.value)}"
        cocotb.log.info("Passed address: %s", addr)
