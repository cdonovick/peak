from hwtypes.adt import Enum, Sum, Product
from hwtypes.modifiers import new
from peak.bitfield import bitfield

from hwtypes import BitVector, Bit

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

Word = new(BitVector, 16, name='Word')

Reg4 = new(BitVector, 4, name='Reg4')
RegA = bitfield(8)(new(BitVector, 4, name='RegA'))
RegB = bitfield(4)(new(BitVector, 4, name='RegB'))
Imm  = bitfield(0)(new(BitVector, 8, name='Imm'))

@bitfield(8)
class Cond(Enum):
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

class ALU(Product):
    ra=RegA
    rb=RegB

class Mov(ALU):
    pass

class And(ALU):
    pass

class Or(ALU):
    pass

class XOr(ALU):
    pass

@bitfield(12)
class Logic(Sum[Mov, And, Or, XOr]): pass


class Add(ALU):
    pass

class Sub(ALU):
    pass

class Adc(ALU):
    pass

class Sbc(ALU):
    pass

@bitfield(12)
class Arith(Sum[Add, Sub, Adc, Sbc]): pass


class _Memory(Product):
    ra  = RegA
    imm = Imm

class LDLO(_Memory):
    pass

class LDHI(_Memory):
    pass

class LD(_Memory):
    pass

class ST(_Memory):
    pass

@bitfield(12)
class Memory(Sum[LDLO, LDHI, LD, ST]): pass


class _Control(Product):
    imm  = Imm
    cond = Cond

class Jump(_Control):
    pass

class Call(_Control):
    pass

class Return(_Control):
    pass

@bitfield(12)
class Control(Sum[Jump, Call, Return]): pass


@bitfield(14)
class Inst(Sum[Logic, Arith, Memory, Control, Word]): pass

