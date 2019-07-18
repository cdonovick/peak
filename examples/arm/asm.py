from .isa import *

R0 = 0
R1 = 1
R2 = 2
R3 = 3
R4 = 4
R5 = 5
R6 = 6
R7 = 7
R8 = 8
R9 = 9
R10 = 10
R11 = 11
R12 = 12
R13 = 13
R14 = 14
R15 = 15

LR = R14
PC = R15

def _imm(val):
    def rol(w,n):
        bits = w.bits()
        return Word(bits[n:] + bits[:n])
    w = Word(val)
    for i in range(16):
        r = rol(w,2*i)
        if r < 256:
            return r[:Rotate.size], i
    raise ValueError(f"Can't convert {val} to an immediate")

def data(Op, ra, rb, rc, shift, imm, s, cond):
    ra = RegA(ra)
    rb = RegB(rb)
    s = S(s)
    if rc is None:
        rotate, imm = _imm(imm)
        rc = Operand(ImmOperand(Imm(imm),Rotate(rotate)))
    else:
        rc = Operand(RegOperand(RegC(rc),Shift(shift)))
    return Inst(BaseInst(Data(Op(ra,rb,rc,s))),cond)

def mov(ra, rb, rc=None, shift=0, imm=0, s=0, cond=Cond.Always):
    return data(MOV, ra, rb, rc=rc, shift=shift, imm=imm, s=s, cond=cond)

def add(ra, rb, rc=None, shift=0, imm=0, s=0, cond=Cond.Always):
    return data(ADD, ra, rb, rc=rc, shift=shift, imm=imm, s=s, cond=cond)

def and_(ra, rb, rc=None, shift=0, imm=0, s=0, cond=Cond.Always):
    return data(AND, ra, rb, rc=rc, shift=shift, imm=imm, s=s, cond=cond)

def or_(ra, rb, rc=None, shift=0, imm=0, s=0, cond=Cond.Always):
    return data(ORR, ra, rb, rc=rc, shift=shift, imm=imm, s=s, cond=cond)

def eor(ra, rb, rc=None, shift=0, imm=0, s=0, cond=Cond.Always):
    return data(EOR, ra, rb, rc=rc, shift=shift, imm=imm, s=s, cond=cond)


def b(offset, link=0, cond=Cond.Always):
    offset = Offset(offset)
    link = L(link)
    return Inst(BaseInst(B(offset,link, BI(1))),cond)


def ldst(Op, ra, rb, rc, shift, imm, cond):
    ra = RegA(ra)
    rb = RegB(rb)
    if rc is None:
        imm, rotate = _imm(imm)
        rc = Operand(ImmOperand(Imm(imm),Rotate(rotate)))
    else:
        rc = Operand(RegOperand(RegC(rc),Shift(shift)))
    return Inst(BaseInst(LDST(Op(ra,rb,rc))),cond)

def ldr(ra, rb, rc=None, shift=0, imm=0, cond=Cond.Always):
    return ldst(LDR, ra, rb, rc, shift, imm, cond)

def str(ra, rb, rc=None, shift=0, imm=0, cond=Cond.Always):
    return ldst(STR, ra, rb, rc, shift, imm, cond)
