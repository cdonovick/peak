Data
- Shift field has more structure

LDST 
- Lots of flags 
  - LD/ST
  - I
  - W write back!
  - pre-increment/post-increment
- Operand is different than Data instructions

cs107e blink.s

// configure GPIO 20 for output
ldr r0, FSEL2
mov r1, #1
str r1, [r0]

// set bit 20
mov r1, #(1<<20)

loop:

// set GPIO 20 high
ldr r0, SET0
str r1, [r0]

// delay
mov r2, #DELAY
wait1:
    subs r2, #1
    bne wait1

// set GPIO 20 low
ldr r0, CLR0
str r1, [r0]

// delay
mov r2, #DELAY
wait2:
    subs r2, #1
    bne wait2

b loop

FSEL0: .word 0x20200000
FSEL1: .word 0x20200004
FSEL2: .word 0x20200008
SET0:  .word 0x2020001C
SET1:  .word 0x20200020
CLR0:  .word 0x20200028
CLR1:  .word 0x2020002C

