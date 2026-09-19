.section .text.init
.globl _start

_start:
    la t0, message
    li t1, 0x10000000

print_next:
    lbu t2, 0(t0)
    beqz t2, finish
    sb t2, 0(t1)
    addi t0, t0, 1
    j print_next

finish:
    li t1, 0x100000
    li t2, 0x5555
    sw t2, 0(t1)

wait_forever:
    wfi
    j wait_forever

.section .rodata
message:
    .asciz "OSLAB_SMOKE_OK\n"
