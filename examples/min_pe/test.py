from hwtypes import Product, Sum, Enum, Tuple
from hwtypes import BitVector
from hwtypes import SMTBitVector
from peak.assembler import Assembler
from peak.assembler import AssembledADT

from sim import gen_sim

from magma.ssa import ssa
import operator

Word, Bit, Inst, sim = gen_sim(BitVector.get_family())
AssembledInst = AssembledADT[Inst, Assembler, BitVector]
assembler = Assembler(Inst)

T = Tuple[Word, Bit]
S = Sum[Word, T]

def nand(x, y):
    return ~(x & y)

x = Word(8)
y = Word(9)
inst = Inst(Inst.Opcode.A, x, S(T(y, Bit(1))))
asm_inst = AssembledInst(inst)
assert inst.operand_1.match(T)
assert ~inst.operand_1.match(Word)
assert x == inst.operand_0
assert y == inst.operand_1[T][0]
res = sim(asm_inst)
assert nand(x, y) == res, (nand(x, y), res, x-y)

def phi(args, s):
    return s.ite(*args)

def Not():
    return operator.inv

sim = ssa(phi=phi)(sim)
res = sim(asm_inst)
assert nand(x, y) == res, (nand(x, y), res, x-y)

