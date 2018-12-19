from dataclasses import dataclass
from peak import Bit, Bits, Enum, Sum, Product
from peak.bitfield import bitfield

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
RegA = bitfield(8)(Bits(4))
RegB = bitfield(4)(Bits(4))

Imm = bitfield(0)(Bits(8))

@bitfield(12)
class Arith_Op(Enum):
    Add = 0
    Sub = 1
    Adc = 2
    Sbc = 3

@bitfield(12)
class Logic_Op(Enum):
    Mov = 0
    And = 1
    Or  = 2
    XOr = 3

@bitfield(8)
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
class LogicInst(Product):
    op:Logic_Op
    ra:RegA
    rb:RegB

@dataclass
class ArithInst(Product):
    op:Arith_Op
    ra:RegA
    rb:RegB

@dataclass
class LDLO(Product):
    ra:RegA
    imm:Imm

@dataclass
class LDHI(Product):
    ra:RegA
    imm:Imm

@dataclass
class LD(Product):
    ra:RegA
    imm:Imm

@dataclass
class ST(Product):
    ra:RegA
    imm:Imm

@bitfield(12)
class MemInst(Sum):
    fields = (LDLO, LDHI, LD, ST)


@dataclass
class Jump(Product):
    imm:Imm
    cond:Cond_Op

@dataclass
class Call(Product):
    imm:Imm
    cond:Cond_Op

@dataclass
class Return(Product):
    cond:Cond_Op

@bitfield(12)
class ControlInst(Sum):
    fields = (Jump, Call, Return)


@bitfield(14)
class Inst(Sum):
    fields = (LogicInst, ArithInst, MemInst, ControlInst)

def logicinst(op, ra, rb):
    return Inst(LogicInst(op, RegA(ra), RegB(rb)))
    
def mov(ra,rb):
    return logicinst(Logic_Op.Mov, ra, rb)
def and_(ra, rb):
    return logicinst(Logic_Op.And, ra, rb)
def or_(ra, rb):
    return logicinst(Logic_Op.Or, ra, rb)
def xor(ra, rb):
    return logicinst(Logic_Op.XOr, ra, rb)

def arithinst(op, ra, rb):
    return Inst(ArithInst(op, RegA(ra), RegB(rb)))
    
def add(ra, rb):
    return arithinst(Arith_Op.Add, ra, rb)
def sub(ra, rb):
    return arithinst(Arith_Op.Sub, ra, rb)
def adc(ra, rb):
    return arithinst(Arith_Op.Adc, ra, rb)
def sbc(ra, rb):
    return arithinst(Arith_Op.Sbc, ra, rb)

def ldlo(ra, imm):
    return Inst(MemInst(LDLO(RegA(ra), Imm(imm))))
def ldhi(ra, imm):
    return Inst(MemInst(LDHI(RegA(ra), Imm(imm))))
def st(ra, imm):
    return Inst(MemInst(ST(RegA(ra), Imm(imm))))

def jmp(imm, cond=Cond_Op.Always):
    return Inst(ControlInst(Jump(Imm(imm), cond)))
def call(imm, cond=Cond_Op.Always):
    return Inst(ControlInst(Call(Imm(imm), cond)))
def ret(cond=Cond_Op.Always):
    return Inst(ControlInst(Return(cond)))

