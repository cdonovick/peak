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


def add(rd, rs1, rs2):
    return Inst(alu=ALU(alur=ALUR(add=Add(RD(rd), RS1(rs1), RS2(rs2)))))

def sub(rd, rs1, rs2):
    return Inst(alu=ALU(alur=ALUR(sub=Sub(RD(rd), RS1(rs1), RS2(rs2)))))

def and_(rd, rs1, rs2):
    return Inst(alu=ALU(alur=ALUR(and_=And(RD(rd), RS1(rs1), RS2(rs2)))))

def or_(rd, rs1, rs2):
    return Inst(alu=ALU(alur=ALUR(or_=Or(RD(rd), RS1(rs1), RS2(rs2)))))

def xor(rd, rs1, rs2):
    return Inst(alu=ALU(alur=ALUR(xor=XOr(RD(rd), RS1(rs1), RS2(rs2)))))


def addi(rd, rs1, imm):
    return Inst(alu=ALU(alui=ALUI(addi=AddI(RD(rd), RS1(rs1), Immed12(int(imm))))))

def andi(rd, rs1, imm):
    return Inst(alu=ALU(alui=ALUI(andi=AndI(RD(rd), RS1(rs1), Immed12(int(imm))))))

def ori(rd, rs1, imm):
    return Inst(alu=ALU(alui=ALUI(ori=OrI(RD(rd), RS1(rs1), Immed12(int(imm))))))

def xori(rd, rs1, imm):
    return Inst(alu=ALU(alui=ALUI(xori=XOrI(RD(rd), RS1(rs1), Immed12(int(imm))))))

def nop():
    return addi(0, 0, 0)


def lui(rd, imm):
    return Inst(lui=LUI(RD(rd), Immed20(int(imm))))


def lw(rd, rs1, imm):
    return Inst(memory=Memory(lw=LW(RD(rd), RS1(rs1), Immed12(int(imm)))))

def sw(rs1, rs2, imm):
    return Inst(memory=Memory(sw=SW(RS1(rs1), RS2(rs2), Immed12(int(imm)))))


def beq(rs1, rs2, imm):
    return Inst(branch=Branch(beq=BEQ(RS1(rs1), RS2(rs2), Immed12(int(imm)>>1))))

def bne(rs1, rs2, imm):
    return Inst(branch=Branch(bne=BNE(RS1(rs1), RS2(rs2), Immed12(int(imm)>>1))))

def blt(rs1, rs2, imm):
    return Inst(branch=Branch(blt=BLT(RS1(rs1), RS2(rs2), Immed12(int(imm)>>1))))

def bge(rs1, rs2, imm):
    return Inst(branch=Branch(bge=BGE(RS1(rs1), RS2(rs2), Immed12(int(imm)>>1))))

def bltu(rs1, rs2, imm):
    return Inst(branch=Branch(bltu=BLTU(RS1(rs1), RS2(rs2), Immed12(int(imm)>>1))))

def bgeu(rs1, rs2, imm):
    return Inst(branch=Branch(bgeu=BGEU(RS1(rs1), RS2(rs2), Immed12(int(imm)>>1))))

