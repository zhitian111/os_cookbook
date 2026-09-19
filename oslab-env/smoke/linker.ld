OUTPUT_ARCH(riscv)
ENTRY(_start)

SECTIONS
{
  /* OpenSBI occupies the low firmware window and hands off here in S-mode. */
  . = 0x80200000;
  .text : { *(.text.init) *(.text*) }
  .rodata : { *(.rodata*) }
  .data : { *(.data*) }
  .bss : { *(.bss*) *(COMMON) }
}
