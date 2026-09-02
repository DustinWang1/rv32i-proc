import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge

@cocotb.test()
async def rf_test(dut):
    Clock(dut.clk, 3, unit="ns").start()

    # Test write function and combinational read.
    dut.wa3.value = 3
    dut.wd.value = 1
    dut.we.value = 1
    await RisingEdge(dut.clk)
    dut.wa3.value = 0
    dut.wd.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)
    dut.a1.value = 3
    dut.a2.value = 1
    await Timer(1, 'ns')
    assert int(dut.r1.value) == 1
    assert int(dut.r2.value) == 0

    # Test register zero is always zero even with write
    await RisingEdge(dut.clk)
    dut.a1.value = 0
    await Timer(1, 'ns')
    assert int(dut.r1.value) == 0
    dut.wa3.value = 0
    dut.wd.value = 1
    dut.we.value = 1
    await RisingEdge(dut.clk)
    dut.wa3.value = 0
    dut.wd.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, 'ns')
    assert int(dut.r1.value) == 0





