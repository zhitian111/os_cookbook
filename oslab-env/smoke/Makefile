RISCV_GCC ?= riscv64-unknown-elf-gcc
BUILD_DIR := build
TARGET := $(BUILD_DIR)/oslab-smoke.elf

.PHONY: all clean

all: $(TARGET)

$(TARGET): start.S linker.ld | $(BUILD_DIR)
	$(RISCV_GCC) -march=rv64imac -mabi=lp64 -nostdlib -nostartfiles \
		-ffreestanding -Wl,-T,linker.ld -Wl,--build-id=none -o $@ start.S

$(BUILD_DIR):
	mkdir -p $@

clean:
	rm -rf $(BUILD_DIR)
	rm -f rust/*.a
