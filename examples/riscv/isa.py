from hwtypes import BitVector, Bit
from hwtypes.adt import Enum, Sum, Product
from hwtypes.modifiers import new
from peak.bitfield import bitfield

WIDTH = 32
Byte = new(BitVector, 8, name="Byte")
Half = new(BitVector, 16, name="Half")
Word = new(BitVector, 32, name="Word")
Reg5 = BitVector[5]

RD = bitfield(7)(new(BitVector, 5, name="RD"))
RS1 = bitfield(15)(new(BitVector, 5, name="RS1"))
RS2 = bitfield(20)(new(BitVector, 5, name="RS2"))
Immed20 = bitfield(12)(new(BitVector, 20, name="Immed20"))
Immed12 = bitfield(20)(new(BitVector, 12, name="Immed12"))
Size = bitfield(12)(new(BitVector, 2, name="Size"))

class LD(Product):
    rd = RD
    rs1 = RS1
    imm = Immed12

class LW(LD): pass

class ST(Product):
    rs1 = RS1
    rs2 = RS2
    imm = Immed12

class SW(ST): pass

class Memory(Sum[LW, SW]): pass


class _Branch(Product):
    rs1 = RS1
    rs2 = RS2
    imm = Immed12

class BEQ(_Branch): pass
class BNE(_Branch): pass
class BLT(_Branch): pass
class BGE(_Branch): pass
class BLTU(_Branch): pass
class BGEU(_Branch): pass

class Branch(Sum[BEQ, BNE, BLT, BGE, BLTU, BGEU]): pass
    

class _ALUR(Product):
    rd = RD
    rs1 = RS1
    rs2 = RS2

class And(_ALUR): pass
class Or(_ALUR): pass
class XOr(_ALUR): pass
class Add(_ALUR): pass
class Sub(_ALUR): pass

class ALUR(Sum[And, Or, XOr, Add, Sub]): pass

class _ALUI(Product):
    rd = RD
    rs1 = RS1
    imm = Immed12

class AndI(_ALUI): pass
class OrI(_ALUI): pass
class XOrI(_ALUI): pass
class AddI(_ALUI): pass
class SubI(_ALUI): pass

class ALUI(Sum[AndI, OrI, XOrI, AddI, SubI]): pass

class ALU(Sum[ALUR, ALUI]): pass

class LUI(Product):
    rd = RD
    imm = Immed20

class Inst(Sum[Memory, Branch, ALU, LUI]): pass

# Missing shift and set instructions
