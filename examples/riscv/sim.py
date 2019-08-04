from hwtypes import BitVector, overflow
from .isa import *
from peak import Peak, gen_register, gen_RAM

MAX_MEMORY = 256
MAX_REGISTERS = 32

class R32I(Peak):

    def __init__(self, mem):
        family = Bit.get_family()

        self.mem = gen_RAM(Inst, depth=MAX_MEMORY)(mem, default_init=Word(0))
        self.reg = gen_RAM(Word, depth=MAX_REGISTERS)([], default_init=Word(0))
        self.pc = gen_register(Word)(Word(0))

    def __call__(self):
        pc = self.pc(0,0)
        inst = self.read_mem(pc)
        pc = pc + 4
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
                res = SInt32(rs1) < SInt32(rs2) 
            elif type == BGE: 
                res = SInt32(rs1) >= SInt32(rs2) 
            elif type == BLTU:
                res = rs1 < rs2
            elif type == BGEU:
                res = rs1 >= rs2
            if res:
                offset = inst.imm.sext(20) << 1
                pc = pc - 4 + offset # pc-4 because pc = pc + 4, see above
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
        # word addressable
        return self.mem(addr >> 2, 0, 0)

    def write_mem(self, addr, data):
        # word addressable
        return self.mem(addr >> 2, data, 1)


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
