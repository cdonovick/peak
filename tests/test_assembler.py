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
    """
    This test takes a function `cond` that is generic (e.g. uses `Cond.Z`) and
    runs the AST rewrite logic to replace uses of the `Cond` enum type with the
    assembled value (using `ISABuilderAssembler` which is the core logic of
    `assemble_values_in_func`).
    """
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

    def cond_expected(code: Cond, alu: Bit, lut: Bit, Z: Bit, N: Bit, C: Bit, V: Bit) ->Bit:
        if code == 0:
            return Z
        elif code == 1:
            return not Z
        elif code == 2 or code == 2:
            return C
        elif code == 3 or code == 3:
            return not C
        elif code == 4:
            return N
        elif code == 5:
            return not N
        elif code == 6:
            return V
        elif code == 7:
            return not V
        elif code == 8:
            return C and not Z
        elif code == 9:
            return not C or Z
        elif code == 10:
            return N == V
        elif code == 11:
            return N != V
        elif code == 12:
            return not Z and N == V
        elif code == 13:
            return Z or N != V
        elif code == 15:
            return alu
        elif code == 14:
            return lut

    peak_cond = gen_cond(Enum)
    assembler, disassembler, width, layout = \
        generate_assembler(peak_cond)
    func_def = m.ast_utils.get_ast(cond).body[0]
    assemblers = {
        Cond: (peak_cond, assembler)
    }
    func_def = ISABuilderAssembler(assemblers, locals(), globals()).visit(func_def)
    assert [ast.dump(s) for s in func_def.body] == \
        [ast.dump(s) for s in m.ast_utils.get_ast(cond_expected).body[0].body]

    # Call the front end to make sure it works
    cond = assemble_values_in_func(assemblers, cond, locals(), globals())

def test_enum_determinism():
    def assemble():
        class ALUOP(Enum):
            Add = new_instruction()
            Sub = new_instruction()
            Or =  new_instruction()
            And = new_instruction()
            XOr = new_instruction()

        assembler, disassembler, width, layout =  generate_assembler(ALUOP)
        instr_bv = assembler(ALUOP.Or)
        return int(instr_bv)
    val = assemble()
    for _ in range(100):
        assert val == assemble()

def test_product_determinism():
    def assemble():
        class ALUOP(Enum):
            Add = new_instruction()
            Sub = new_instruction()
            Or =  new_instruction()
            And = new_instruction()
            XOr = new_instruction()

        class Inst(Product):
            alu_op1 = ALUOP
            alu_op2 = ALUOP

        assembler, disassembler, width, layout =  generate_assembler(Inst)
        instr_bv = assembler(Inst(ALUOP.Add, ALUOP.Sub))
        return int(instr_bv)
    val = assemble()
    for _ in range(100):
        assert val == assemble()

def test_sum_determinism():
    def assemble():
        class OP1(Enum):
            Add = new_instruction()
            Sub = new_instruction()

        class OP2(Enum):
            Or =  new_instruction()
            And = new_instruction()
            XOr = new_instruction()


        class Inst(Sum[OP1, OP2]): pass

        assembler, disassembler, width, layout =  generate_assembler(Inst)
        add_instr = Inst(OP1.Add)
        instr_bv = assembler(add_instr)
        return int(instr_bv)

    val = assemble()
    for _ in range(100):
        assert val == assemble()
