import pytest

from hwtypes import Bit, BitVector
from hwtypes.adt import Enum, Product

from peak import Const, family_closure, Peak, name_outputs
from peak import family
from peak.assembler.assembler import Assembler
from peak.assembler.assembled_adt import AssembledADT
from peak.mapper import ArchMapper, RewriteRule
from peak.mapper.index_var import OneHot, Binary

from examples.reg_file import sim as regsim
from examples.smallir import gen_SmallIR
from examples.sum_pe.sim import PE_fc as PE_fc_s, ISA_fc as ISA_fc_s
from examples.tagged_pe.sim import PE_fc as PE_fc_t, ISA_fc as ISA_fc_t

from examples.riscv import family as riscv_family
from examples.riscv import sim as riscv_sim


num_test_vectors = 16


@pytest.mark.parametrize('simple_formula', [True, False])
def test_simple(simple_formula):
    print()
    @family_closure
    def ir_fc(family):
        Data = BitVector[8]
        @family.assemble(locals(), globals())
        class IR(Peak):
            @name_outputs(out=Data)
            def __call__(self, in0: Data, in1: Data):
                return in0 + in1
        return IR

    #Simple PE that can only add or not
    @family_closure
    def arch_fc(family):
        Data = BitVector[8]
        class Inst(Product):
            class Op(Enum):
                add = 1
                not_ = 2

        @family.assemble(locals(), globals())
        class Arch(Peak):
            def __call__(self, inst: Const(Inst), a: Data, b: Data) -> Data:
                if inst.Op == Inst.Op.add:
                    return a + b
                else: #inst == Inst.not_
                    return ~a
        return Arch

    arch_mapper = ArchMapper(arch_fc)
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc, simple_formula)
    rewrite_rule = ir_mapper.solve('z3', external_loop=True)
    assert rewrite_rule is not None

    #verify the mapping works
    counter_example = rewrite_rule.verify()
    assert counter_example is None


@pytest.mark.parametrize('IVar', [OneHot, Binary])
@pytest.mark.parametrize('simple_formula', [True, False])
@pytest.mark.parametrize('external_loop', [True, False])
@pytest.mark.parametrize('arch_fc', [PE_fc_s, PE_fc_t])
def test_automapper(IVar, simple_formula, external_loop, arch_fc):
    IR = gen_SmallIR(8)
    arch_bv = arch_fc(family.PyFamily())
    arch_mapper = ArchMapper(arch_fc, IVar=IVar)
    expect_found = ('Add', 'Sub', 'And', 'Nand', 'Or', 'Nor')
    expect_not_found = ('Mul', 'Shftr', 'Shftl', 'Not', 'Neg')
    for ir_name, ir_fc in IR.instructions.items():
        ir_mapper = arch_mapper.process_ir_instruction(ir_fc, simple_formula)
        rewrite_rule = ir_mapper.solve('z3', external_loop=external_loop)
        if rewrite_rule is None:
            assert ir_name in expect_not_found
            continue
        assert ir_name in expect_found
        #verify the mapping works
        counter_example = rewrite_rule.verify()
        assert counter_example is None
        ir_bv = ir_fc(family.PyFamily())
        ir_paths, arch_paths = rewrite_rule.get_input_paths()
        for _ in range(num_test_vectors):
            ir_vals = {path: BitVector.random(8) for path in ir_paths}
            arch_vals = {path: BitVector.random(8) for path in arch_paths}
            ir_inputs, arch_inputs = rewrite_rule.build_inputs(ir_vals, arch_vals, family.PyFamily())
            assert ir_bv()(**ir_inputs) == arch_bv()(**arch_inputs)[0]


@pytest.mark.parametrize('simple_formula', [True, False])
@pytest.mark.parametrize('external_loop', [True, False])
def test_reg(simple_formula, external_loop):
    IR = gen_SmallIR(32)
    family = riscv_family
    arch_bv = regsim.RegPE_fc.Py()
    arch_mapper = ArchMapper(regsim.RegPE_mappable_fc, family=riscv_family)
    expect_found = frozenset(('Add', 'Nor', 'Not'))
    expect_not_found = IR.instructions.keys() - expect_found

    for ir_name, ir_fc in IR.instructions.items():
        ir_mapper = arch_mapper.process_ir_instruction(ir_fc, simple_formula)
        rewrite_rule = ir_mapper.solve('z3', external_loop=external_loop)
        if rewrite_rule is None:
            assert ir_name in expect_not_found
            continue
        assert ir_name in expect_found

        #verify the mapping works
        counter_example = rewrite_rule.verify()
        assert counter_example is None
        ir_bv = ir_fc(family.PyFamily())
        ir_paths, arch_paths = rewrite_rule.get_input_paths()
        for _ in range(num_test_vectors):
            ir_vals = {path: BitVector.random(8) for path in ir_paths}
            arch_vals = {path: BitVector.random(8) for path in arch_paths}
            ir_inputs, arch_inputs = rewrite_rule.build_inputs(ir_vals, arch_vals, family.PyFamily())
            rs1 = arch_inputs['rs1']
            rs2 = arch_inputs['rs2']
            inst = arch_inputs['inst']
            if inst.b.match:
                binst = inst.b.value
                # Hack to fix instruction where idx1 == idx2 but rs1 != rs2
                idx1 = binst.rs1
                idx2 = binst.rs2
                if idx1 != 0 and idx2 != 0 and rs1 != rs2:
                    while idx1 == idx2 or idx2 == 0:
                        idx2 += 1
                arch_bv.register_file.store(idx1, rs1)
                arch_bv.register_file.store(idx2, rs2)
                rd = binst.rd

                Inst = type(inst)
                # rebuild the instruction
                inst = Inst(b=Inst.b(op=binst.op, rs1=idx1, rs2=idx2, rd=rd))
            else:
                uinst = inst.u.value
                arch_bv.register_file.store(uinst.rs1, rs1)
                rd = uinst.rd

            arch_bv(inst)
            assert ir_bv()(**ir_inputs) == arch_bv.register_file.load1(rd)


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
        class Inst(Product):
            class Op(Enum):
                add = 1
                sub = 2
            sel=family.Bit
        @family.assemble(locals(), globals())
        class Arch(Peak):
            def __call__(self, inst : Const(Inst), a: Data, b: Data) -> (Data, Data):
                if inst.Op == Inst.Op.add:
                    ret = a + b
                else: #inst == Inst.sub
                    ret = a - b
                if inst.sel:
                    return ret, ret
                else:
                    return ~ret, ~ret
        return Arch, Inst


    Inst_bv = PE_fc(family.PyFamily())[1]
    Inst_adt = AssembledADT[Inst_bv, Assembler, BitVector]

    ir_fc = coreir_add_fc
    arch_fc = family_closure(lambda f: PE_fc(f)[0]) #Only return peak class
    output_binding = [(("out",), (0,))]

    #Test correct rewrite rule
    input_binding = [
        (("in0",), ("a",)),
        (("in1",), ("b",)),
        (Inst_adt.Op(Inst_bv.Op.add)._value_, ("inst", "Op",)),
        (Bit(1), ("inst", "sel",)),
    ]
    rr = RewriteRule(input_binding, output_binding, ir_fc, arch_fc)
    assert rr.verify() is None

    #Test incorrect rewrite rule
    input_binding = [
        (("in0",), ("a",)),
        (("in1",), ("b",)),
        (Inst_adt.Op(Inst_bv.Op.sub)._value_, ("inst", "Op",)),
        (Bit(0), ("inst", "sel",)),
    ]
    rr = RewriteRule(input_binding, output_binding, ir_fc, arch_fc)
    counter_example = rr.verify()
    assert counter_example is not None

    #Show that counter example is in fact a counter example
    ir_vals, arch_vals = counter_example
    ir_inputs, arch_inputs = rr.build_inputs(ir_vals, arch_vals, family.PyFamily())
    ir_bv = ir_fc.Py
    arch_bv = PE_fc.Py[0]
    assert ir_bv()(**ir_inputs) != arch_bv()(**arch_inputs)[0]


#This will test the const modifier
@pytest.mark.parametrize('simple_formula', [True, False])
def test_const(simple_formula):

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
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc, simple_formula)
    rr = ir_mapper.solve('z3')
    assert rr is not None
    assert (('const_value',), ('inst', 'imm')) in rr.ibinding


#This will test the const modifier without the name_outputs
@pytest.mark.parametrize('simple_formula', [True, False])
def test_const_tuple(simple_formula):

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
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc, simple_formula)
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


def run_constraint_test(arch_fc, ir_fc, constraints, solved, simple_formula):
    arch_bv = arch_fc(family.PyFamily())
    arch_mapper = ArchMapper(arch_fc, path_constraints=constraints)
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc, simple_formula)
    assert ir_mapper.has_bindings
    rr = ir_mapper.solve('z3')
    if rr is None:
        assert not solved
    else:
        assert solved


@pytest.mark.parametrize('simple_formula', [True, False])
@pytest.mark.parametrize('arch_fc, ISA_fc, is_sum', [
    (PE_fc_s, ISA_fc_s, True),
    (PE_fc_t, ISA_fc_t, False),
    ])
def test_const_constraint(simple_formula, arch_fc, ISA_fc, is_sum):
    @family_closure
    def ir_fc(family):
        Data = BitVector[8]

        @family.assemble(locals(), globals())
        class IR(Peak):
            @name_outputs(out=Data)
            def __call__(self, in0: Data, in1: Data):
                return in0 + in1 + 4  # inst.offset should be 4

        return IR

    isa = ISA_fc.Py

    for constraint, solved in (
        (4, True),
        ((4, 5), True),
        (5, False),
        ((3, 5), False),
    ):
        if is_sum:
            constraints = {("inst", isa.ArithOp, 1): constraint}
        else:
            constraints = {("inst", 'alu', 1): constraint}

        run_constraint_test(arch_fc, ir_fc, constraints=constraints, solved=solved, simple_formula=simple_formula)

    OpT = isa.Op
    for constraint, solved in (
        (OpT.A, True),
        ((OpT.A, OpT.B), True),
        (OpT.B, False),
    ):
        if is_sum:
            constraints = {("inst", isa.ArithOp, 0): constraint}
        else:
            constraints = {("inst", 'alu', 0): constraint}
        run_constraint_test(arch_fc, ir_fc, constraints=constraints, solved=solved, simple_formula=simple_formula)


@pytest.mark.parametrize('simple_formula', [True, False])
@pytest.mark.parametrize('arch_fc, ISA_fc, is_sum', [
    (PE_fc_s, ISA_fc_s, True),
    (PE_fc_t, ISA_fc_t, False),
    ])
def test_non_const_constraint(simple_formula, arch_fc, ISA_fc, is_sum):
    @family_closure
    def ir_fc(family):
        Data = family.BitVector[8]

        @family.assemble(locals(), globals())
        class IR(Peak):
            @name_outputs(out=Data)
            def __call__(self, in0: Data):
                return in0

        return IR

    isa = ISA_fc.Py
    OpT = isa.Op
    for in0_constraint, solved in (
        (-5, True),
        (-4, False),
        ((-5, -4), False),
    ):
        if is_sum:
            constraints = {
                ("inst", isa.ArithOp, 0): OpT.A,  # Const
                ("inst", isa.ArithOp, 1): 5,  # Const
                ("in0",): in0_constraint,  # Not Const
            }
        else:
            constraints = {
                ("inst", 'alu', 0): OpT.A,  # Const
                ("inst", 'alu', 1): 5,  # Const
                ("in0",): in0_constraint,  # Not Const
            }
        run_constraint_test(arch_fc, ir_fc, constraints=constraints, solved=solved, simple_formula=simple_formula)

@pytest.mark.parametrize('simple_formula', [True, False])
def test_riscv_rr(simple_formula):
    @family_closure
    def ir_fc(family):
        Data = family.BitVector[32]
        @family.assemble(locals(), globals())
        class i32_add(Peak):
            def __call__(self, in0: BitVector[32], in1: BitVector[32]) -> BitVector[32]:
                return in0 + in1
        return i32_add

    arch_fc = riscv_sim.R32I_mappable_fc
    arch_mapper = ArchMapper(arch_fc, family=riscv_family)
    ir_mapper = arch_mapper.process_ir_instruction(ir_fc, simple_formula=simple_formula)
    rewrite_rule = ir_mapper.solve('z3', external_loop=True)
    assert rewrite_rule is not None
    ce = rewrite_rule.verify()
    assert ce is None
