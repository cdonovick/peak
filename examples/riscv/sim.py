from hwtypes import BitVector, overflow
from .isa import *
from peak import Peak, gen_register2, RAM

MAX_MEMORY = 256
MAX_REGISTERS = 32

class R32I(Peak):

    def __init__(self, mem):
        family = Bit.get_family()

        self.mem = RAM(Inst, MAX_MEMORY, mem, Word(0))
        self.reg = RAM(Word, MAX_REGISTERS, [], Word(0))
        self.pc = gen_register2(family, Word, Word(0))()

    def __call__(self):
        pc = self.pc(0,0)
        inst = self.read_mem(pc)
        pc = pc + 4

        if inst.alu.match:
            alu = inst.alu.value
            if   alu.alur.match:
                alur = alu.alur.value
                if   alur.add.match:
                    add = alur.add.value
                    rs1 = self.read_reg(add.rs1)
                    rs2 = self.read_reg(add.rs2)
                    rd = add.rd
                    res = rs1 + rs2
                elif alur.sub.match:
                    sub = alur.sub.value
                    rs1 = self.read_reg(sub.rs1)
                    rs2 = self.read_reg(sub.rs2)
                    rd = sub.rd
                    res = rs1 - rs2
                elif alur.and_.match:
                    and_ = alur.and_.value
                    rs1 = self.read_reg(and_.rs1)
                    rs2 = self.read_reg(and_.rs2)
                    rd = and_.rd
                    res = rs1 & rs2
                elif alur.or_.match:
                    or_ = alur.or_.value
                    rs1 = self.read_reg(or_.rs1)
                    rs2 = self.read_reg(or_.rs2)
                    rd = or_.rd
                    res = rs1 | rs2
                elif alur.xor.match:
                    xor = alur.xor.value
                    rs1 = self.read_reg(xor.rs1)
                    rs2 = self.read_reg(xor.rs2)
                    rd = xor.rd
                    res = rs1 ^ rs2
                self.write_reg(rd, res)
            elif alu.alui.match:
                alui = alu.alui.value
                if   alui.addi.match:
                    add = alui.addi.value
                    rs1 = self.read_reg(add.rs1)
                    imm = add.imm.sext(20)
                    rd = add.rd
                    res = rs1 + imm
                elif alui.andi.match:
                    andi = alui.andi.value
                    rs1 = self.read_reg(andi.rs1)
                    imm = andi.imm.sext(20)
                    rd = andi.rd
                    res = rs1 & imm
                elif alui.ori.match:
                    ori = alui.ori.value
                    rs1 = self.read_reg(ori.rs1)
                    imm = ori.imm.sext(20)
                    rd = ori.rd
                    res = rs1 | imm
                elif alui.xori.match:
                    xori = alui.xori.value
                    rs1 = self.read_reg(xori.rs1)
                    imm = xori.imm.sext(20)
                    rd = xori.rd
                    res = rs1 ^ imm
                self.write_reg(rd, res)
        elif inst.lui.match:
            lui = inst.lui.value
            imm = lui.imm.zext(12) << 12 # 20-bit immediate
            self.write_reg(lui.rd, imm)
        elif inst.memory.match:
            mem = inst.memory.value
            if   mem.lw.match:
                lw = mem.lw.value
                rs1 = self.read_reg(lw.rs1)
                imm = lw.imm.sext(20) 
                addr = rs1 + imm
                data = self.read_mem(addr)
                self.write_reg(lw.rd, data)
            elif mem.sw.match:
                sw = mem.sw.value
                rs1 = self.read_reg(sw.rs1)
                imm = sw.imm.sext(20) 
                data = self.read_reg(sw.rs2)
                addr = rs1 + imm
                self.write_mem(addr, data)
        elif inst.branch.match:
            branch = inst.branch.value
            if   branch.beq.match:
                beq = branch.beq.value
                rs1 = self.read_reg(beq.rs1)
                rs2 = self.read_reg(beq.rs2)
                imm = beq.imm
                res = rs1 == rs2
            elif branch.bne.match:
                bne = branch.bne.value
                rs1 = self.read_reg(bne.rs1)
                rs2 = self.read_reg(bne.rs2)
                imm = bne.imm
                res = rs1 != rs2
            elif branch.blt.match:
                blt = branch.blt.value
                rs1 = self.read_reg(blt.rs1)
                rs2 = self.read_reg(blt.rs2)
                imm = blt.imm
                res = SInt32(rs1) < SInt32(rs2) 
            elif branch.bge.match:
                bge = branch.bge.value
                rs1 = self.read_reg(bge.rs1)
                rs2 = self.read_reg(bge.rs2)
                imm = bge.imm
                res = SInt32(rs1) >= SInt32(rs2) 
            elif branch.bltu.match:
                bltu = branch.bltu.value
                rs1 = self.read_reg(bltu.rs1)
                rs2 = self.read_reg(bltu.rs2)
                imm = bltu.imm
                res = rs1 < rs2
            elif branch.bgeu.match:
                bgeu = branch.bgeu.value
                rs1 = self.read_reg(bgeu.rs1)
                rs2 = self.read_reg(bgeu.rs2)
                imm = bgeu.imm
                res = rs1 >= rs2
            if res:
                offset = imm.sext(20) << 1
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
