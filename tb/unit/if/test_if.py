import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge

@cocotb.test()
async def if_test(dut):
    Clock(dut.clk, 1, unit="ns").start()

    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    # Test expected sequence
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 0x00000013
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 0
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 1
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 2
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 3

    # Test stall
    dut.stall.value = 1
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 4
    assert int(dut.pcF.value) == 16
    assert int(dut.nextPcF.value) == 20
    dut.stall.value = 0
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 4
    assert int(dut.pcF.value) == 16
    assert int(dut.nextPcF.value) == 20
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 5
    assert int(dut.pcF.value) == 20
    assert int(dut.nextPcF.value) == 24

    # Test flush
    dut.flush.value = 1
    dut.pcSrc.value = 1
    dut.jumpAddr.value = 4
    await RisingEdge(dut.clk)
    dut.flush.value = 0
    dut.pcSrc.value = 0
    dut.jumpAddr.value = 0
    assert int(dut.instrF.value) == 0x00000013
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 0x00000013
    assert int(dut.pc.value) == 4
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 1

    # Test rst
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 0x00000013
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 0x00000013
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 0x00000013
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 0x00000013
    assert int(dut.pc.value) == 0
    await RisingEdge(dut.clk)
    assert int(dut.instrF.value) == 0
    assert int(dut.pc.value) == 4

    
    
    
    

    
