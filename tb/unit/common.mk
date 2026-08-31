SIM ?= verilator
TOPLEVEL_LANG = verilog
EXTRA_ARGS += --trace --trace-structs
include $(shell cocotb-config --makefiles)/Makefile.sim