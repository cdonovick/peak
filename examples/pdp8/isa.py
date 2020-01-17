from hwtypes.adt import Enum, Product, Sum, TaggedUnion
from hwtypes.modifiers import new
#from peak.bitfield import tag
from hwtypes import BitVector, Bit

WIDTH = 12
Word = BitVector[WIDTH]

# Direct vs indirect addressing
class IA(Enum): 
    DIRECT = 0
    INDIRECT = 1

# Page
class MP(Enum): 
    PAGE_ZERO = 0
    CURRENT_PAGE = 1

Addr= BitVector[7]

class MRI(Product):
    i = IA
    p = MP
    addr = Addr

class AND(MRI): pass
class TAD(MRI): pass
class ISZ(MRI): pass
class DCA(MRI): pass
class JMS(MRI): pass
class JMP(MRI): pass

class IOT(Product):
    i = IA
    p = MP
    addr = Addr

class OPR1(Product):
    cla = Bit # clear accumulator 1
    cll = Bit # clear link 1
    cma = Bit # complement accumulator 2
    cml = Bit # complelemnt link 2
    rar = Bit # rotate right 4
    ral = Bit # rotate left 4
    twice = Bit # rotate twice / byte swap if ral==rar=0
    iac = Bit # increment accumulator 3

class OPR2(Product):
    cla = Bit # clear accumulator 2
    sma = Bit # skip on minus (negastive) accumulator 1
    sza = Bit # skip on zero accumulator 1
    snl = Bit # skip on non-zero link 1
    skip = Bit # reverse skip 1
    osr = Bit # or switch register with accumulator 2
    hlt = Bit # halt 3
    NOP = Bit # 0 if ORP2, 1 if OPR2

#@tag({OPR1:0, OPR2:1})
class OPR(TaggedUnion):
    opr1 = OPR1
    opr2 = OPR2

#@tag({AND:0, TAD:1, ISZ:2, DCA:3, JMS:4, JMP:5, IOT:6, OPR:7})
class Inst(TaggedUnion):
    and_ = AND
    tad = TAD
    isz = ISZ
    dca = DCA
    jms = JMS
    jmp = JMP
    iot = IOT
    opr = OPR
