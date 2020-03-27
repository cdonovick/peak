from hwtypes import Bit, BitVector
from hwtypes.adt import Enum, Product
from peak.mapper.utils import pretty_print_binding
from peak.mapper import ArchMapper
from peak import Const, family_closure, Peak, name_outputs, assemble
from examples.sum_pe.sim import PE_fc
from examples.smallir import gen_SmallIR
import pytest

num_test_vectors = 16
def test_automapper():
    IR = gen_SmallIR(8)
    arch_fc = PE_fc
    arch_bv = arch_fc(Bit.get_family())
    arch_mapper = ArchMapper(arch_fc)
    expect_found = ('Add', 'Sub', 'And', 'Nand', 'Or', 'Nor', 'Not', 'Neg')
    expect_not_found = ('Mul', 'Shftr', 'Shftl')
    for ir_name, ir_fc in IR.instructions.items():
        ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
        solution = ir_mapper.solve('z3')
        if not solution.solved:
            assert ir_name in expect_not_found
            continue
        assert ir_name in expect_found
        #verify the mapping works
        ir_bv = ir_fc(Bit.get_family())
        for _ in range(num_test_vectors):
            ir_vals = {path:BitVector.random(8) for path in solution.ir_bounded}
            ir_inputs = solution.build_ir_input(ir_vals)
            arch_inputs = solution.build_arch_input(ir_vals)
            assert ir_bv()(**ir_inputs) == arch_bv()(**arch_inputs)


#This will test the const modifier
def test_const():

    #Testing out something like coreir const
    @family_closure
    def IR_fc(family):
        Data = family.BitVector[16]

        @assemble(family, locals(), globals())
        class IR(Peak):
            @name_outputs(out=Data)
            def __call__(self, const_value : Const(Data)):
                return const_value
        return IR

    @family_closure
    def Arch_fc(family):
        Data = family.BitVector[16]
        class Op(Enum):
            add = 1
            const = 2
        class Inst(Product):
            op = Op
            imm = Data

        @assemble(family, locals(), globals())
        class Arch(Peak):
            @name_outputs(out=Data)
            def __call__(self, inst : Const(Inst), in0 : Data, in1 : Data):
                if inst.op == Op.add:
                    return in0 + in1
                else: #inst.op == Op.const
                    return inst.imm
        return Arch

    arch_fc = Arch_fc
    arch_bv = arch_fc(Bit.get_family())
    arch_mapper = ArchMapper(arch_fc)
    ir_fc = IR_fc
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
    solution = ir_mapper.solve('z3')
    assert solution.solved
    assert (('const_value',), ('inst', 'imm')) in solution.ibinding

#This will test the const modifier without the name_outputs
def test_const_tuple():

    #Testing out something like coreir const
    @family_closure
    def IR_fc(family):
        Data = family.BitVector[16]
        @assemble(family, locals(), globals())
        class IR(Peak):
            def __call__(self, const_value : Const(Data)) -> Data:
                return const_value
        return IR

    @family_closure
    def Arch_fc(family):
        Data = family.BitVector[16]
        class Op(Enum):
            add = 1
            const = 2
        class Inst(Product):
            op = Op
            imm = Data

        @assemble(family, locals(), globals())
        class Arch(Peak):
            def __call__(self, inst : Const(Inst), in0 : Data, in1 : Data) -> Data:
                if inst.op == Op.add:
                    return in0 + in1
                else: #inst.op == Op.const
                    return inst.imm
        return Arch

    arch_fc = Arch_fc
    arch_bv = arch_fc(Bit.get_family())
    arch_mapper = ArchMapper(arch_fc)
    ir_fc = IR_fc
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
    solution = ir_mapper.solve('z3')
    assert solution.solved
    assert (('const_value',), ('inst', 'imm')) in solution.ibinding

def test_early_out_inputs():
    @family_closure
    def IR_fc(family):
        Data = family.BitVector[16]

        @assemble(family, locals(), globals())
        class IR(Peak):
            @name_outputs(out=Data)
            def __call__(self, const_value : Const(Data)):
                return const_value
        return IR

    @family_closure
    def Arch_fc(family):
        Data = family.BitVector[16]
        @assemble(family, locals(), globals())
        class Arch(Peak):
            @name_outputs(out=Data)
            def __call__(self, in0 : Data, in1 : Data):
                return in0 + in1
        return Arch

    arch_fc = Arch_fc
    arch_bv = arch_fc(Bit.get_family())
    arch_mapper = ArchMapper(arch_fc)
    ir_fc = IR_fc
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
    solution = ir_mapper.solve('z3')
    assert not solution.solved
    assert not ir_mapper.has_bindings

def test_early_out_outputs():
    @family_closure
    def IR_fc(family):
        Data = family.BitVector[16]
        @assemble(family, locals(), globals())
        class IR(Peak):
            @name_outputs(out=Data)
            def __call__(self, in_: Data):
                return in_
        return IR

    @family_closure
    def Arch_fc(family):
        Data = family.BitVector[16]
        Bit = family.Bit
        @assemble(family, locals(), globals())
        class Arch(Peak):
            @name_outputs(out=Bit)
            def __call__(self, in_ : Data):
                return in_[0]
        return Arch

    arch_fc = Arch_fc
    arch_bv = arch_fc(Bit.get_family())
    arch_mapper = ArchMapper(arch_fc)
    ir_fc = IR_fc
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
    solution = ir_mapper.solve('z3')
    assert not solution.solved
    assert not ir_mapper.has_bindings


@pytest.mark.parametrize("opts", (
    (None, True),
    ((0, 1, 2), False),
    ((4, 5), True)))
def test_constrain_constant_bv(opts):
    constraint = opts[0]
    solved = opts[1]
    arch_fc = PE_fc
    arch_bv = arch_fc(Bit.get_family())
    arch_mapper = ArchMapper(arch_fc, constrain_constant_bv=constraint)

    @family_closure
    def ir_fc(family):
        Data = family.BitVector[8]
        @assemble(family, locals(), globals())
        class IR(Peak):
            @name_outputs(out=Data)
            def __call__(self, in0: Data, in1: Data):
                return in0 + in1 + 4 #inst.offset should be 4
        return IR
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
    assert ir_mapper.has_bindings
    solution = ir_mapper.solve('z3')
    if solution.solved:
        pretty_print_binding(solution.ibinding)
    assert solution.solved == solved
