from dataclasses import dataclass
from peak import Bit, Bits, Enum

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
    Z = 0
    Z_n = 1
    C = 2
    C_n = 3
    N = 4
    N_n = 5
    V = 6
    V_n = 7
    Hi = 8
    Ls = 9
    GE = 10
    LT = 11
    GT = 12
    LE = 13
    Any = 14

@dataclass
class LogicInst:
    op:Logic_Op
    ra:RegA = RegA(0)
    rb:RegB = RegB(0)

    def __call__(self, ra, rb):
        self.ra = RegA(ra)
        self.rb = RegB(rb)
        return self

@dataclass
class ArithInst:
    op:Arith_Op
    ra:RegA = RegA(0)
    rb:RegB = RegB(0)

    def __call__(self, ra, rb):
        self.ra = RegA(ra)
        self.rb = RegB(rb)
        return self

ALUInst = (ArithInst, LogicInst)

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

MemInst = (LDLO, LDHI, LD, ST)


@dataclass
class Jump:
    imm:Imm
    cond:Cond_Op = Cond_Op.Any

    def __call__(self, imm):
        self.imm = Byte(imm)
        return self

@dataclass
class Call:
    imm:Imm
    cond:Cond_Op = Cond_Op.Any

    def __call__(self, imm):
        self.imm = Byte(imm)
        return self

@dataclass
class Ret:
    cond:Cond_Op = Cond_Op.Any

ControlInst = (Jump, Call, Ret)


Inst = (LogicInst, ArithInst, MemInst, ControlInst)


mov = LogicInst(op=Logic_Op.Mov)
and_ = LogicInst(op=Logic_Op.And)
or_ = LogicInst(op=Logic_Op.Or)
xor = LogicInst(op=Logic_Op.XOr)

ldlo = LDLO
ldhi = LDHI

jmp = Jump

#print(mov(0,1))
#print(ldlo(0,10))
#print(jmp(10))
