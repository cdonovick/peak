from .isa import *

x0 = 0
x1 = 1
x2 = 2
x3 = 3
x4 = 4
x5 = 5
x6 = 6
x7 = 7
x8 = 8
x9 = 9
x10 = 10
x11 = 11
x12 = 12
x13 = 13
x14 = 14
x15 = 15
x16 = 16
x17 = 17
x18 = 18
x19 = 19
x20 = 20
x21 = 21
x22 = 22
x23 = 23
x24 = 24
x25 = 25
x26 = 26
x27 = 27
x28 = 28
x29 = 29
x30 = 30
x31 = 31

zero = 0
ra = x1
sp = x2
gp = x3
tp = x4
t0 = x5
t1 = x6
t2 = x7
fp = x8
s0 = x8
s1 = x9
a0 = x10
a1 = x11
a2 = x12
a3 = x13
a4 = x14
a5 = x15
a6 = x16
a7 = x17


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
    return Inst(ALU(ALUI(op(RD(rd), RS1(rs1), Immed12(int(imm))))))

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
    return Inst(LUI(RD(rd), Immed20(int(imm))))


def lw(rd, rs1, imm):
    return Inst(Memory(LW(RD(rd), RS1(rs1), Immed12(int(imm)))))

def sw(rs1, rs2, imm):
    return Inst(Memory(SW(RS1(rs1), RS2(rs2), Immed12(int(imm)))))


def b(cond, rs1, rs2, imm):
    return Inst(Branch(cond(RS1(rs1), RS2(rs2), Immed12(int(imm)>>1))))

def beq(rs1, rs2, imm):
    return b(BEQ, rs1, rs2, imm)

def bne(rs1, rs2, imm):
    return b(BNE, rs1, rs2, imm)

def blt(rs1, rs2, imm):
    return b(BLT, rs1, rs2, imm)

def bge(rs1, rs2, imm):
    return b(BGE, rs1, rs2, imm)

def bltu(rs1, rs2, imm):
    return b(BLTU, rs1, rs2, imm)

def bgeu(rs1, rs2, imm):
    return b(BGEU, rs1, rs2, imm)

