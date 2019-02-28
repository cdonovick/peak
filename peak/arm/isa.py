from peak import new, Enum, Sum, Product
from peak.bitfield import bitfield
from hwtypes import BitVector, Bit


Byte = new(BitVector, 8)
Half = new(BitVector, 16)
Word = new(BitVector, 32)

Imm = bitfield(0)(new(BitVector, 8))
Rotate = bitfield(8)(new(BitVector, 4))

class ImmOperand(Product):
    imm:Imm
    rotate:Rotate

RegC = bitfield(0)(new(BitVector, 4))
Shift = bitfield(4)(new(BitVector, 8))

class RegOperand(Product):
    rc:RegC
    shift:Shift

@bitfield(25)
class Operand(Sum[RegOperand, ImmOperand]): pass

RegA = bitfield(16)(new(BitVector, 4))
RegB = bitfield(12)(new(BitVector, 4))
S = bitfield(20)(new(BitVector, 1))

class _Data(Product):
    ra:RegA
    rb:RegB
    rc:Operand
    s:S

class AND(_Data):
    pass

class EOR(_Data):
    pass

class SUB(_Data):
    pass

class RSB(_Data):
    pass

class ADD(_Data):
    pass

class ADC(_Data):
    pass

class SBC(_Data):
    pass

class RSC(_Data):
    pass

class TST(_Data):
    pass

class TEQ(_Data):
    pass

class CMP(_Data):
    pass

class CMN(_Data):
    pass

class ORR(_Data):
    pass

class MOV(_Data):
    pass

class BIC(_Data):
    pass

class MVN(_Data):
    pass

@bitfield(21)
class Data(Sum[AND, EOR, SUB, RSB, ADD, ADC, SBC, RSC,
    TST, TEQ, CMP, CMN, ORR, MOV, BIC, MVN]): pass

class _LDST(Product):
    ra:RegA
    rb:RegB
    rc:Operand

class LDR(_LDST):
    pass

class STR(_LDST):
    pass

@bitfield(20)
class LDST(Sum[STR, LDR]): pass


Offset = bitfield(0)(new(BitVector, 24))
L = bitfield(24)(new(BitVector, 1))
BI = bitfield(25)(new(BitVector, 1))

class B(Product):
    offset:Offset
    l:L
    i:BI = BI(1)

@bitfield(28)
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
    Always = 14

@bitfield(26)
class BaseInst(Sum[Data, LDST, B]): pass

class Inst(Product):
    inst:BaseInst
    cond:Cond

