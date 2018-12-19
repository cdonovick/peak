from dataclasses import dataclass
from peak import Bit, Bits, Enum, Sum

#word 16
#registers 16

#0000aaaabbbb0000 "mov"
#0001aaaabbbb0000 "and_"
#0010aaaabbbb0000 "or_"
#0011aaaabbbb0000 "xor"

#0100aaaabbbb0000 "add"
#0101aaaabbbb0000 "sub"
#0110aaaabbbb0000 "adc"
#0111aaaabbbb0000 "sbc"

#1000aaaaiiiiiiii "ldlo"
#1001aaaaiiiiiiii "ldhi"
#1010aaaaiiiiiiii "ld"
#1011aaaaiiiiiiii "st"
#
#1100cccciiiiiiii "jmpc" 
#1101cccciiiiiiii "callc"
#1110cccc00000000 "retc"

Nibble = Bits(4)
Byte = Bits(8)
Half = Bits(16)
Word = Half

Reg4 = Nibble
RegA = Reg4
RegB = Reg4

Imm = Byte

class Arith_Op(Enum):
    Add = 0
    Sub = 1
    Adc = 2
    Sbc = 3

class Logic_Op(Enum):
    Mov = 0
    And = 1
    Or  = 2
    XOr = 3

class Cond_Op(Enum):
    Z = 0    # EQ
    Z_n = 1  # NE
    C = 2    # UGE
    C_n = 3  # ULT
    N = 4    # <  0
    N_n = 5  # >= 0
    V = 6    # Overflow
    V_n = 7  # No overflow
    UGE = 2
    ULT = 3
    UGT = 8
    ULE = 9
    SGE = 10
    SLT = 11
    SGT = 12
    SLE = 13
    Never = 14
    Always = 15

@dataclass
class LogicInst:
    op:Logic_Op
    ra:RegA
    rb:RegB

@dataclass
class ArithInst:
    op:Arith_Op
    ra:RegA
    rb:RegB

@dataclass
class LDLO:
    ra:RegA
    imm:Imm

@dataclass
class LDHI:
    ra:RegA
    imm:Imm

@dataclass
class LD:
    ra:RegA
    imm:Imm

@dataclass
class ST:
    ra:RegA
    imm:Imm

class MemInst(Sum):
    fields = (LDLO, LDHI, LD, ST)


@dataclass
class Jump:
    imm:Imm
    cond:Cond_Op

@dataclass
class Call:
    imm:Imm
    cond:Cond_Op

@dataclass
class Return:
    cond:Cond_Op

class ControlInst(Sum):
    fields = (Jump, Call, Return)


class Inst(Sum):
    fields = (LogicInst, ArithInst, MemInst, ControlInst)

def mov(ra,rb):
    return Inst(LogicInst(Logic_Op.Mov, ra, rb))
def and_(ra, rb):
    return Inst(LogicInst(Logic_Op.And, ra, rb))
def or_(ra, rb):
    return Inst(LogicInst(Logic_Op.Or, ra, rb))
def xor(ra, rb):
    return Inst(LogicInst(Logic_Op.XOr, ra, rb))

def add(ra, rb):
    return Inst(ArithInst(Arith_Op.Add, ra, rb))
def sub(ra, rb):
    return Inst(ArithInst(Arith_Op.Sub, ra, rb))
def adc(ra, rb):
    return Inst(ArithInst(Arith_Op.Adc, ra, rb))
def sbc(ra, rb):
    return Inst(ArithInst(Arith_Op.Sbc, ra, rb))

def ldlo(ra, imm):
    return Inst(MemInst(LDLO(ra, imm)))
def ldhi(ra, imm):
    return Inst(MemInst(LDHI(ra, imm)))
def st(ra, imm):
    return Inst(MemInst(ST(ra, imm)))

def jmp(imm, cond=Cond_Op.Always):
    return Inst(ControlInst(Jump(imm, cond)))
def call(imm, cond=Cond_Op.Always):
    return Inst(ControlInst(Call(imm, cond)))
def ret(cond=Cond_Op.Always):
    return Inst(ControlInst(Return(cond)))

