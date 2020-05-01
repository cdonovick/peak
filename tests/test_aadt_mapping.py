from peak.assembler.assembler import Assembler
from peak.assembler.assembled_adt import  AssembledADT
from hwtypes import Bit, BitVector
from hwtypes.adt import Enum, Product
from peak.mapper import ArchMapper, RewriteRule
from peak import Const, family_closure, Peak, name_outputs
from peak import family
from examples.sum_pe.sim import PE_fc
from examples.smallir import gen_SmallIR
import pytest

num_test_vectors = 16
def test_automapper():
    IR = gen_SmallIR(8)
    arch_fc = PE_fc
    arch_bv = arch_fc(family.PyFamily())
    arch_mapper = ArchMapper(arch_fc)
    expect_found = ('Add', 'Sub', 'And', 'Nand', 'Or', 'Nor', 'Not', 'Neg')
    expect_not_found = ('Mul', 'Shftr', 'Shftl')
    for ir_name, ir_fc in IR.instructions.items():
        ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
        rewrite_rule = ir_mapper.solve('z3')
        if rewrite_rule is None:
            assert ir_name in expect_not_found
            continue
        assert ir_name in expect_found
        #verify the mapping works
        counter_example = rewrite_rule.verify()
        assert counter_example is None
        ir_bv = ir_fc(family.PyFamily())
        for _ in range(num_test_vectors):
            ir_vals = {path:BitVector.random(8) for path in rewrite_rule.ir_bounded}
            ir_inputs = rewrite_rule.build_ir_input(ir_vals, family.PyFamily())
            arch_inputs = rewrite_rule.build_arch_input(ir_vals, family.PyFamily())
            assert ir_bv()(**ir_inputs) == arch_bv()(**arch_inputs)

def test_custom_rr():

    #This is like a CoreIR Add
    @family_closure
    def coreir_add_fc(family):
        Data = family.BitVector[16]
        @family.assemble(locals(), globals())
        class IR(Peak):
            @name_outputs(out=Data)
            def __call__(self, in0: Data, in1: Data):
                return in0 + in1
        return IR

    #Simple PE that can only add or subtract
    @family_closure
    def PE_fc(family):
        Data = family.BitVector[16]
        class Inst(Enum):
            add = 1
            sub = 2

        @family.assemble(locals(), globals())
        class Arch(Peak):
            def __call__(self, inst : Const(Inst), a: Data, b: Data) -> (Data, Data):
                if inst == Inst.add:
                    return a + b, a
                else: #inst == Inst.sub
                    return a - b, a
        return Arch, Inst


    Inst_bv = PE_fc(family.PyFamily())[1]
    Inst_adt = AssembledADT[Inst_bv, Assembler, BitVector]

    ir_fc = coreir_add_fc
    arch_fc = lambda f: PE_fc(f)[0] #Only return peak class
    output_binding = [(("out",), (0,))]

    #Test correct rewrite rule
    input_binding = [
        (("in0",), ("a",)),
        (("in1",), ("b",)),
        (Inst_adt(Inst_bv.add)._value_, ("inst",)),
    ]
    rr = RewriteRule(input_binding, output_binding, ir_fc, arch_fc)
    assert rr.verify() is None

    #Test incorrect rewrite rule
    input_binding = [
        (("in0",), ("a",)),
        (("in1",), ("b",)),
        (Inst_adt(Inst_bv.sub)._value_, ("inst",)),
    ]
    rr = RewriteRule(input_binding, output_binding, ir_fc, arch_fc)
    counter_example = rr.verify()
    assert counter_example is not None

    #Show that counter example is in fact a counter example
    ir_vals = counter_example
    ir_inputs = rr.build_ir_input(ir_vals, family.PyFamily())
    arch_inputs = rr.build_arch_input(ir_vals, family.PyFamily())
    ir_bv = ir_fc(family.PyFamily())
    arch_bv = arch_fc(family.PyFamily())
    assert ir_bv()(**ir_inputs) != arch_bv()(**arch_inputs)[0]


#This will test the const modifier
def test_const():

    #Testing out something like coreir const
    @family_closure
    def IR_fc(family):
        Data = family.BitVector[16]

        @family.assemble(locals(), globals())
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

        @family.assemble(locals(), globals())
        class Arch(Peak):
            @name_outputs(out=Data)
            def __call__(self, inst : Const(Inst), in0 : Data, in1 : Data):
                if inst.op == Op.add:
                    return in0 + in1
                else: #inst.op == Op.const
                    return inst.imm
        return Arch

    arch_fc = Arch_fc
    arch_bv = arch_fc(family.PyFamily())
    arch_mapper = ArchMapper(arch_fc)
    ir_fc = IR_fc
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
    rr = ir_mapper.solve('z3')
    assert rr is not None
    assert (('const_value',), ('inst', 'imm')) in rr.ibinding

#This will test the const modifier without the name_outputs
def test_const_tuple():

    #Testing out something like coreir const
    @family_closure
    def IR_fc(family):
        Data = family.BitVector[16]
        @family.assemble(locals(), globals())
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

        @family.assemble(locals(), globals())
        class Arch(Peak):
            def __call__(self, inst : Const(Inst), in0 : Data, in1 : Data) -> Data:
                if inst.op == Op.add:
                    return in0 + in1
                else: #inst.op == Op.const
                    return inst.imm
        return Arch

    arch_fc = Arch_fc
    arch_bv = arch_fc(family.PyFamily())
    arch_mapper = ArchMapper(arch_fc)
    ir_fc = IR_fc
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
    rr = ir_mapper.solve('z3')
    assert rr is not None
    assert (('const_value',), ('inst', 'imm')) in rr.ibinding

def test_early_out_inputs():
    @family_closure
    def IR_fc(family):
        Data = family.BitVector[16]

        @family.assemble(locals(), globals())
        class IR(Peak):
            @name_outputs(out=Data)
            def __call__(self, const_value : Const(Data)):
                return const_value
        return IR

    @family_closure
    def Arch_fc(family):
        Data = family.BitVector[16]
        @family.assemble(locals(), globals())
        class Arch(Peak):
            @name_outputs(out=Data)
            def __call__(self, in0 : Data, in1 : Data):
                return in0 + in1
        return Arch

    arch_fc = Arch_fc
    arch_bv = arch_fc(family.PyFamily())
    arch_mapper = ArchMapper(arch_fc)
    ir_fc = IR_fc
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
    rr = ir_mapper.solve('z3')
    assert rr is None
    assert not ir_mapper.has_bindings

def test_early_out_outputs():
    @family_closure
    def IR_fc(family):
        Data = family.BitVector[16]
        @family.assemble(locals(), globals())
        class IR(Peak):
            @name_outputs(out=Data)
            def __call__(self, in_: Data):
                return in_
        return IR

    @family_closure
    def Arch_fc(family):
        Data = family.BitVector[16]
        Bit = family.Bit
        @family.assemble(locals(), globals())
        class Arch(Peak):
            @name_outputs(out=Bit)
            def __call__(self, in_ : Data):
                return in_[0]
        return Arch

    arch_fc = Arch_fc
    arch_bv = arch_fc(family.PyFamily())
    arch_mapper = ArchMapper(arch_fc)
    ir_fc = IR_fc
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
    rr = ir_mapper.solve('z3')
    assert rr is None
    assert not ir_mapper.has_bindings


@pytest.mark.parametrize("opts", (
    (None, True),
    ((0, 1, 2), False),
    ((4, 5), True)))
def test_constrain_constant_bv(opts):
    constraint = opts[0]
    solved = opts[1]
    arch_fc = PE_fc
    arch_bv = arch_fc(family.PyFamily())
    arch_mapper = ArchMapper(arch_fc, constrain_constant_bv=constraint)

    @family_closure
    def ir_fc(family):
        Data = family.BitVector[8]
        @family.assemble(locals(), globals())
        class IR(Peak):
            @name_outputs(out=Data)
            def __call__(self, in0: Data, in1: Data):
                return in0 + in1 + 4 #inst.offset should be 4
        return IR
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc)
    assert ir_mapper.has_bindings
    rr = ir_mapper.solve('z3')
    if rr is None:
        assert not solved
    else:
        assert solved
