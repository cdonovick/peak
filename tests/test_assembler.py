from peak.auto_assembler import generate_assembler, ISABuilderAssembler, \
    assemble_values_in_func
from peak.demo_pes.pe5.isa import INST as pe5_isa
from peak.arm.isa import Inst as arm_isa
from peak.pico.isa import Inst as pico_isa
from hwtypes import BitVector
from hwtypes.adt import Product, Sum, Enum, new_instruction
import inspect
import magma as m
import ast

import pytest

@pytest.mark.parametrize("isa", [pe5_isa, arm_isa, pico_isa])
def test_assembler_disassembler(isa):
    assembler, disassembler, width, layout =  generate_assembler(isa)
    for inst in isa.enumerate():
        opcode = assembler(inst)
        assert isinstance(opcode, BitVector[width])
        assert disassembler(opcode) == inst

        if isinstance(isa, Product):
            for name,field in isa._fields_dict.items():
                e,d,w,l = generate_assembler(field)
                assert l == layout[name][2]
                sub_opcode = opcode[layout[name][0] : layout[name][1]]
                assert sub_opcode.size <= w
                assert isinstance(d(sub_opcode), field)
        elif isinstance(isa, Sum):
            for field in isa.fields:
                e,d,w,l = generate_assembler(field)
                assert l == layout[field][2]
                sub_opcode = opcode[layout[field][0] : layout[field][1]]
                assert sub_opcode.size <= w
                assert isinstance(d(sub_opcode), field)

    if isinstance(isa, Product):
        for name,field in isa._fields_dict.items():
            e,d,w,l = generate_assembler(field)
            for inst in field.enumerate():
                opcode = e(inst)
                assert isinstance(opcode, BitVector[w])
                assert d(opcode) == inst
    elif isinstance(isa, Sum):
        for field in isa.fields:
            e,d,w,l = generate_assembler(field)
            for inst in field.enumerate():
                opcode = e(inst)
                assert isinstance(opcode, BitVector[w])
                assert d(opcode) == inst


def test_ast_rewrite():
    def gen_cond(enum):
        class Cond(enum):
            Z = 0    # EQ
            Z_n = 1  # NE
            C = 2    # UGE
            C_n = 3  # ULT
            N = 4    # <  0
            N_n = 5  # >= 0
            V = 6    # Overflow
            V_n = 7  # No overflow
            EQ = 0
            NE = 1
            UGE = 2
            ULT = 3
            UGT = 8
            ULE = 9
            SGE = 10
            SLT = 11
            SGT = 12
            SLE = 13
            LUT = 14
            ALU = 15
        return Cond

    Bit = m.Bit
    Cond = gen_cond(m.Enum)
    def cond(code: Cond, alu: Bit, lut: Bit, Z: Bit, N: Bit, C:
             Bit, V: Bit) -> Bit:
        if code == Cond.Z:
            return Z
        elif code == Cond.Z_n:
            return not Z
        elif code == Cond.C or code == Cond.UGE:
            return C
        elif code == Cond.C_n or code == Cond.ULT:
            return not C
        elif code == Cond.N:
            return N
        elif code == Cond.N_n:
            return not N
        elif code == Cond.V:
            return V
        elif code == Cond.V_n:
            return not V
        elif code == Cond.UGT:
            return C and not Z
        elif code == Cond.ULE:
            return not C or Z
        elif code == Cond.SGE:
            return N == V
        elif code == Cond.SLT:
            return N != V
        elif code == Cond.SGT:
            return not Z and (N == V)
        elif code == Cond.SLE:
            return Z or (N != V)
        elif code == Cond.ALU:
            return alu
        elif code == Cond.LUT:
            return lut

    def cond_expected(code: Cond, alu: Bit, lut: Bit, Z: Bit, N: Bit, C: Bit,
                      V: Bit) -> Bit:
        if code == assemble(Cond.Z):
            return Z
        elif code == assemble(Cond.Z_n):
            return not Z
        elif code == assemble(Cond.C) or code == assemble(Cond.UGE):
            return C
        elif code == assemble(Cond.C_n) or code == assemble(Cond.ULT):
            return not C
        elif code == assemble(Cond.N):
            return N
        elif code == assemble(Cond.N_n):
            return not N
        elif code == assemble(Cond.V):
            return V
        elif code == assemble(Cond.V_n):
            return not V
        elif code == assemble(Cond.UGT):
            return C and not Z
        elif code == assemble(Cond.ULE):
            return not C or Z
        elif code == assemble(Cond.SGE):
            return N == V
        elif code == assemble(Cond.SLT):
            return N != V
        elif code == assemble(Cond.SGT):
            return not Z and (N == V)
        elif code == assemble(Cond.SLE):
            return Z or (N != V)
        elif code == assemble(Cond.ALU):
            return alu
        elif code == assemble(Cond.LUT):
            return lut

    assembler, disassembler, width, layout = \
        generate_assembler(gen_cond(Enum))
    func_def = m.ast_utils.get_ast(cond).body[0]
    func_def = ISABuilderAssembler(locals(), globals()).visit(func_def)
    assert [ast.dump(s) for s in func_def.body] == \
        [ast.dump(s) for s in m.ast_utils.get_ast(cond_expected).body[0].body]

    # Call the front end to make sure it works
    cond = assemble_values_in_func(assembler, cond, locals(), globals())

def test_determinism():
    def foo():
        class ALUOP(Enum):
            Add = new_instruction()
            Sub = new_instruction()
            Or =  new_instruction()
            And = new_instruction()
            XOr = new_instruction()

        class Inst(Product):
            alu_op = ALUOP
        
        assembler, disassembler, width, layout =  generate_assembler(Inst)
        add_instr = Inst(ALUOP.Add)
        instr_bv = assembler(add_instr)
        return int(instr_bv)
    val = foo()
    for i in range(100):
        assert val == foo()
