import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

@cocotb.test()
async def dff_passes_through(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.d.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert dut.q.value == 1
    