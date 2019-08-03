RISCV in Peak

Good summary of the instructons

https://www.imperialviolet.org/2016/12/31/riscv.html

https://rv8.io/isa.html

https://github.com/riscv/riscv-isa-sim/blob/master/riscv/decode.h

https://github.com/ucb-bar/riscv-sodor/


opcode
- R 0b0110011 = 0x33
- I LOAD = 0x03
- SB STORE = 0x23
- B BRANCH = 0x63
- U LUI = ...
- U AUIPC = ...
- UJ JAL = 
- UJ JALR = 

LW instructions are I type
- funct3 stores width and signed 
  - byte=0, half=1, word=2
  - 3rd bit indicates unsigned load
  - no lwu

SW instructions are SB type
  - Immed12 split across two fields
  - func3 stores width
    - byte=0, half=1, word=2

B instructions are B type
  - Immed12 split across two fields
    - bits are shuffled!
  - func3 stores branch type


shift immediate instructions only use 5 bits of immed12
- this leaves 7 bits for other options
