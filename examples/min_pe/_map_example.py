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

def add(a, b):  return a + b
def sub(a, b):  return b - a
def and_(a, b): return a & b
def nand(a, b): return ~(a & b)
def or_(a, b):  return a | b
def nor(a, b):  return ~(b | a)
def mul(a, b):  return a * b
def shftr(a, b): return a >> b
def shftl(a, b): return a << b
targets = (
    add,
    sub,
    and_,
    nand,
    or_,
    nor,
    mul,
    shftr,
    shftl,
)

Word, Bit, Inst, sim = gen_sim(SMTBitVector.get_family())

T = Tuple[Word, Bit]
S = Sum[Word, T]

SMTInst = AssembledADT[Inst, Assembler, SMTBitVector]
assembler = Assembler(Inst)
opcode_asm = assembler.sub.Opcode.asm
operand_1_asm = assembler.sub.operand_1.asm

opcode_bv = SMTBitVector[opcode_asm.width](name='opcode')
tag_bv = SMTBitVector[operand_1_asm.tag_width](name='tag')

#Should be determined automatically
binding = SMTBitVector[4](name='binding')

x = Word(name='x')
y = Word(name='y')
b = Bit(name='b')
free_bit = Bit(name='free_bit')


# abusing knowledge of the layout
# there should be some way to generate this automatically
# like some sort assemble from leaves
inst_bv = (
    (binding == 1).ite(
        # x~operand_0, y~operand_1[T][0]
        opcode_bv.concat(x).concat(tag_bv).concat(y).concat(b),
        (binding == 2).ite(
            # x~operand_0, y~operand_1[Word]
            opcode_bv.concat(x).concat(tag_bv).concat(y).concat(free_bit),
            (binding == 4).ite(
                # y~operand_0, x~operand_1[T][0]
                opcode_bv.concat(y).concat(tag_bv).concat(x).concat(b),
                # y~operand_0, x~operand_1[Word]
                opcode_bv.concat(y).concat(tag_bv).concat(x).concat(free_bit),
            )
        )
    )
)

inst = SMTInst(inst_bv)
precondition = (
    (binding == 1).ite(
        inst.operand_1.match(T),
        (binding == 2).ite(
            inst.operand_1.match(Word),
            (binding == 4).ite(
                inst.operand_1.match(T),
                (binding == 8) & inst.operand_1.match(Word)
            )
        )
    )
)

sim_expr = sim(inst)
for target in targets:
    target_expr = target(x, y)
    with smt.Solver('z3', logic=BV) as solver:
        solver.add_assertion(precondition.value)
        constraint = smt.ForAll([x.value, y.value, free_bit.value], (sim_expr == target_expr).value)
        solver.add_assertion(constraint)
        if solver.solve():
            opcode_val = solver.get_value(opcode_bv.value).constant_value()
            b_val = solver.get_value(b.value).constant_value()
            tag_val = solver.get_value(tag_bv.value).constant_value()
            binding_val = solver.get_value(binding.value).constant_value()
            print(f'mapping found for {target.__name__}')
            print(f'binding: {binding_val}')
            print(f'opcode: {opcode_asm.disassemble(opcode_val)}')
            print(f'tag: {operand_1_asm.disassemble_tag(tag_val)}')
            print(f'b: {b_val}')
            print()
        else:
            print(f'no mapping found for {target.__name__}')
            print()



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
