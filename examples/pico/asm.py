from .isa import *

def logic(op, ra, rb):
    return Inst(Logic(op(RegA(ra), RegB(rb))))

def mov(ra,rb):
    return logic(Mov, ra, rb)
def and_(ra, rb):
    return logic(And, ra, rb)
def or_(ra, rb):
    return logic(Or, ra, rb)
def xor(ra, rb):
    return logic(XOr, ra, rb)

def arith(op, ra, rb):
    return Inst(Arith(op(RegA(ra), RegB(rb))))

def add(ra, rb):
    return arith(Add, ra, rb)
def sub(ra, rb):
    return arith(Sub, ra, rb)
def adc(ra, rb):
    return arith(Adc, ra, rb)
def sbc(ra, rb):
    return arith(Sbc, ra, rb)


def memory(op, ra, imm):
    return Inst(Memory(op(RegA(ra), Imm(imm))))

def ldlo(ra, imm):
    return memory(LDLO, ra, imm)
def ldhi(ra, imm):
    return memory(LDHI, ra, imm)
def st(ra, imm):
    return memory(ST, ra, imm)


def control(op, imm, cond):
    return Inst(Control(op(Imm(imm),cond)))

def jmp(imm, cond=Cond.Always):
    return control(Jump, imm, cond)
def call(imm, cond=Cond.Always):
    return control(Call, imm, cond)
def ret(cond=Cond.Always):
    return control(Return, 0, cond)

