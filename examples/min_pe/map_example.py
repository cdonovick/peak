from hwtypes import Product, Sum, Enum, Tuple
from hwtypes import SMTBitVector, SMTBit
from peak.assembler import Assembler
from peak.assembler import AssembledADT

from sim import gen_sim

from ast_tools.passes import begin_rewrite, end_rewrite, debug
from ast_tools.passes import ssa, bool_to_bit, if_to_phi
import operator


import pysmt.shortcuts as smt
from pysmt.logics import BV


def nand(x, y):
    return ~(x & y)

Word, Bit, Inst, sim = gen_sim(SMTBitVector.get_family())

T = Tuple[Word, Bit]
S = Sum[Word, T]

SMTInst = AssembledADT[Inst, Assembler, SMTBitVector]
assembler = Assembler(Inst)
opcode_asm = assembler.sub.Opcode.asm
operand_1_asm = assembler.sub.operand_1.asm

opcode_bv = SMTBitVector[opcode_asm.width](name='opcode')
tag_bv = SMTBitVector[operand_1_asm.tag_width](name='tag')

x = Word(name='x')
y = Word(name='y')
b = Bit(name='b')

# abusing some knowledge of the layout
# there should be some way to generate this automatically
# especially the conditional part
inst_bv = opcode_bv.concat(x).concat(tag_bv).concat(
        (tag_bv == operand_1_asm.assemble_tag(T, SMTBitVector)).ite(
            y.concat(b),
            y.concat(Bit(0))
        )
    )
inst = SMTInst(inst_bv)
sim_expr = sim(inst)
nand_expr = nand(x, y)

with smt.Solver('cvc4', logic=BV) as solver:
    constraints = smt.ForAll([x.value, y.value], (sim_expr == nand_expr).value)
    solver.add_assertion(constraints)
    if solver.solve():
        opcode_val = solver.get_value(opcode_bv.value).constant_value()
        b_val = solver.get_value(b.value).constant_value()
        tag_val = solver.get_value(tag_bv.value).constant_value()
        print(f'opcode: {opcode_asm.disassemble(opcode_val)}')
        print(f'tag: {operand_1_asm.disassemble_tag(tag_val)}')
        print(f'b: {b_val}')


# I would like to do things this way
# but it doesn't work for some reason
#
#inst_bv = SMTBitVector[assembler.width](name='inst')
#inst = SMTInst(inst_bv)
#
#preconditions = []
#
#preconditions.append((inst.Opcode == opcode_bv).value) #opcode_bv is inst.opcode
#preconditions.append((inst.operand_0 == x).value) # x is operand_0
#preconditions.append(inst.operand_1.match(tag_bv).value) # tag is the tag of operand_1
#
#preconditions.append(
#        smt.Ite(
#            inst.operand_1.match(T).value, #if operand_1 is a T
#            smt.And(
#                (inst.operand_1[T][0] == y).value,  # y is the BV part of operand1
#                (inst.operand_1[T][1] == b).value,  # b is the bit part of operand1
#            ),
#            smt.And(
#                inst.operand_1.match(Word).value,  # operand_1 is a Word
#                (inst.operand_1[Word] == y).value, # y is the operand_1
#            ),
#        )
#    )
#
