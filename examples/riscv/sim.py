from hwtypes import BitVector, overflow
from .isa import *
from peak import Peak, gen_register, RAM, ROM

MAX_MEMORY = 256
MAX_REGISTERS = 32

class R32I(Peak):

    def __init__(self, mem):
        family = Bit.get_family()
        self.mem = RAM(Inst, MAX_MEMORY, mem, Word(0))

        self.reg = RAM(Word, MAX_REGISTERS, [Word(0) for i in range(MAX_REGISTERS)])

        self.pc = gen_register(family, Word, Word(0))()

    def __call__(self):
        pc = self.pc(0,0)
        inst = self.read_mem(pc)
        pc = pc + 1
        type, inst = inst.match()

        if type == ALU:
            type, inst = inst.match()
            if   type == ALUR:
                type, inst = inst.match()
                rs1 = self.read_reg(inst.rs1)
                rs2 = self.read_reg(inst.rs2)
                if   type == Add:
                    rd = rs1 + rs2
                elif type == Sub:
                    rd = rs1 - rs2
                elif type == And:
                    rd = rs1 & rs2
                elif type == Or:
                    rd = rs1 | rs2
                elif type == XOr:
                    rd = rs1 ^ rs2
                self.write_reg(inst.rd, rd)
            elif type == ALUI:
                type, inst = inst.match()
                rs1 = self.read_reg(inst.rs1)
                imm = inst.imm.sext(20)
                if   type == AddI:
                    rd = rs1 + imm
                elif type == SubI:
                    rd = rs1 - imm
                elif type == AndI:
                    rd = rs1 & imm
                elif type == OrI:
                    rd = rs1 | imm
                elif type == XOrI:
                    rd = rs1 ^ imm
                self.write_reg(inst.rd, rd)
        elif type == LUI:
            imm = inst.imm.zext(12) << 12 # 20-bit immediate
            self.write_reg(inst.rd, imm)
        elif type == Memory:
            type, inst = inst.match()
            rs1 = self.read_reg(inst.rs1)
            imm = inst.imm.sext(20) 
            if   type == LW:
                addr = rs1 + imm
                data = self.read_mem(addr)
                self.write_reg(inst.rd, data)
            elif type == SW:
                addr = rs1 + imm
                data = self.read_reg(inst.rs2)
                self.write_mem(addr, data)
        elif type == Branch:
            type, inst = inst.match()
            rs1 = self.read_reg(inst.rs1)
            rs2 = self.read_reg(inst.rs2)
            if   type == BEQ:
                res = rs1 == rs2
            elif type == BNE:
                res = rs1 != rs2
            elif type == BLT:
                res = rs1 < rs2 # signed
            elif type == BGE: 
                res = rs1 >= rs2 # signed
            elif type == BLTU:
                res = rs1 < rs2
            elif type == BGEU:
                res = rs1 >= rs2
            if res:
                #offset = inst.imm.sext(20) << 1
                offset = inst.imm.sext(20) # memory not byte addressable
                pc = pc - 1 + offset # -1 because pc = pc + 1, see above
        self.pc(pc,1)

    # register interface
    def read_reg(self, reg):
        if reg == 0:
           return Word(0)
        return self.reg(Reg5(reg), 0, 0)

    def write_reg(self, reg, data):
        if reg == 0:
           return Word(0)
        return self.reg(Reg5(reg), data, 1)

    # memory interface
    def read_mem(self, addr):
        return self.mem(addr, 0, 0)

    def write_mem(self, addr, data):
        return self.mem(addr, data, 1)


    # testing interface
    def peak_pc(self):
        return int(self.pc(0,0))

    def poke_pc(self, data):
        return int(self.pc(Word(data),1))

    def peak_reg(self, reg):
        return int(self.read_reg(reg))

    def poke_reg(self, reg, data):
        return int(self.write_reg(reg, Word(data)))

    def peak_mem(self, addr):
        return int(self.read_mem(Word(addr)))

    def poke_mem(self, addr, data):
        return int(self.write_mem(Word(addr), Word(data)))
