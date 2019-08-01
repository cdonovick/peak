from .isa import *

def alur(op, rd, rs1, rs2):
    return Inst(ALU(ALUR(op(RD(rd), RS1(rs1), RS2(rs2)))))

def add(rd, rs1, rs2):
    return alur(Add, rd, rs1, rs2)

def sub(rd, rs1, rs2):
    return alur(Sub, rd, rs1, rs2)

def and_(rd, rs1, rs2):
    return alur(And, rd, rs1, rs2)

def or_(rd, rs1, rs2):
    return alur(Or, rd, rs1, rs2)

def xor(rd, rs1, rs2):
    return alur(XOr, rd, rs1, rs2)


def alui(op, rd, rs1, imm):
    return Inst(ALU(ALUI(op(RD(rd), RS1(rs1), Immed12(imm)))))

def addi(rd, rs1, imm):
    return alui(AddI, rd, rs1, imm)

def subi(rd, rs1, imm):
    return alui(SubI, rd, rs1, imm)

def andi(rd, rs1, imm):
    return alui(AndI, rd, rs1, imm)

def ori(rd, rs1, imm):
    return alui(OrI, rd, rs1, imm)

def xori(rd, rs1, imm):
    return alui(XOrI, rd, rs1, imm)

def nop():
    return addi(0, 0, 0)


def lui(rd, imm):
    return Inst(LUI(RD(rd), Immed20(imm)))


def lw(rd, rs1, imm):
    return Inst(Memory(LW(RD(rd), RS1(rs1), Immed12(imm))))

def sw(rs1, rs2, imm):
    return Inst(Memory(SW(RS1(rs1), RS2(rs2), Immed12(imm))))


def beq(rs1, rs2, imm):
    return Inst(Branch(BEQ(RS1(rs1), RS2(rs2), Immed12(imm))))

def bne(rs1, rs2, imm):
    return Inst(Branch(BNE(RS1(rs1), RS2(rs2), Immed12(imm))))

def blt(rs1, rs2, imm):
    return Inst(Branch(BLT(RS1(rs1), RS2(rs2), Immed12(imm))))

def bge(rs1, rs2, imm):
    return Inst(Branch(BGE(RS1(rs1), RS2(rs2), Immed12(imm))))

def bltu(rs1, rs2, imm):
    return Inst(Branch(BLTU(RS1(rs1), RS2(rs2), Immed12(imm))))

def bgeu(rs1, rs2, imm):
    return Inst(Branch(BGEU(RS1(rs1), RS2(rs2), Immed12(imm))))

