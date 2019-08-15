from hwtypes import SIntVector, UIntVector, BitVector, Bit
from hwtypes.adt import Enum, Sum, Product
from hwtypes.modifiers import new
from peak.bitfield import bitfield, tag

WIDTH = 32
Byte = new(BitVector, 8, name="Byte")
Half = new(BitVector, 16, name="Half")
Word = new(BitVector, 32, name="Word")

UInt32 = new(UIntVector, 32, name="UInt32")
SInt32 = new(SIntVector, 32, name="SInt32")

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

@tag({LW: 0, SW:1})
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

@tag({BEQ: 0, BNE:1, BLT:2, BGE:3, BLTU:4, BGEU:5})
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

@tag({And: 0, Or:1, XOr:2, Add:3, Sub:4})
class ALUR(Sum[And, Or, XOr, Add, Sub]): pass

class _ALUI(Product):
    rd = RD
    rs1 = RS1
    imm = Immed12

class AndI(_ALUI): pass
class OrI(_ALUI): pass
class XOrI(_ALUI): pass
class AddI(_ALUI): pass

@tag({AndI: 0, OrI:1, XOrI:2, AddI:3})
class ALUI(Sum[AndI, OrI, XOrI, AddI]): pass

@tag({ALUR: 0, ALUI:1})
class ALU(Sum[ALUR, ALUI]): pass

class LUI(Product):
    rd = RD
    imm = Immed20

@tag({Memory: 0, Branch:1, ALU:2, LUI:3})
class Inst(Sum[Memory, Branch, ALU, LUI]): pass

# Missing shift and set instructions
