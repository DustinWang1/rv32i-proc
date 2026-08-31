ADDR_WIDTH := 8
DEPTH := $(shell echo $$(( 1 << $(ADDR_WIDTH) )))
PATTERN_HEX := $(PWD)/../../../build/sim/imem_pattern.hex

VERILOG_SOURCES := $(PWD)/../../../rtl/core/fetch.sv $(PWD)/../../../rtl/mem/imem.sv
COCOTB_TOPLEVEL := fetch
COCOTB_TEST_MODULES := test_if

$(PATTERN_HEX): gen_pattern.py
	mkdir -p $(dir $@)
	python3 gen_pattern.py $(DEPTH) > $@

EXTRA_ARGS += -GADDR_WIDTH=$(ADDR_WIDTH)
EXTRA_ARGS += -GINIT_FILE=\"$(PATTERN_HEX)\"

sim: $(PATTERN_HEX)

include ../common.mk