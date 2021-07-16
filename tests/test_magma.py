import pytest
from peak import Peak, family_closure, Const
from peak.assembler import Assembler, AssembledADT
from peak.rtl_utils import wrap_with_disassembler
from peak import family
from peak import name_outputs

from hwtypes import Bit, SMTBit, SMTBitVector, BitVector, Enum, Product, Sum
from examples.demo_pes.pe6 import PE_fc
from examples.demo_pes.pe6.sim import Inst

import fault
import magma
import itertools
import random

N_TESTS = 16


@pytest.mark.parametrize('named_outputs', [True, False])
@pytest.mark.parametrize('set_port_names', [True, False])
def test_basic(named_outputs, set_port_names):
    @family_closure
    def PE_fc(family):
        if named_outputs:
            @family.assemble(locals(), globals(), set_port_names=set_port_names)
            class PENamed(Peak, typecheck=True):
                    @name_outputs(out=Bit)
                    def __call__(self, in0: Bit, in1: Bit) -> Bit:
                        return in0 & in1
            return PENamed
        else:
            @family.assemble(locals(), globals(), set_port_names=set_port_names)
            class PEAnon(Peak, typecheck=True):
                def __call__(self, in0: Bit, in1: Bit) -> Bit:
                    return in0 & in1
            return PEAnon

    #verify BV works
    PE_bv = PE_fc(family.PyFamily())
    vals = [Bit(0), Bit(1)]
    for i0, i1 in itertools.product(vals, vals):
        assert PE_bv()(i0, i1) == i0 & i1

    #verify SMT works
    PE_smt = PE_fc(family.SMTFamily())
    vals = [SMTBit(0), SMTBit(1), SMTBit(), SMTBit()]
    for i0, i1 in itertools.product(vals, vals):
        assert PE_smt()(i0, i1) == i0 & i1

    #verify magma works
    PE_magma = PE_fc(family.MagmaFamily())
    named = named_outputs and set_port_names
    if named:
        assert 'O' not in PE_magma.interface.ports
        assert PE_magma.interface.ports.keys() >= {'in0', 'in1', 'out',}
    else:
        assert 'out' not in PE_magma.interface.ports
        assert PE_magma.interface.ports.keys() >= {'in0', 'in1', 'O',}

    tester = fault.Tester(PE_magma)
    vals = [0, 1]
    for i0, i1 in itertools.product(vals, vals):
        tester.circuit.in0 = i0
        tester.circuit.in1 = i1
        tester.eval()
        if named:
            tester.circuit.out.expect(i0 & i1)
        else:
            tester.circuit.O.expect(i0 & i1)
    tester.compile_and_run("verilator", flags=["-Wno-fatal"])


def test_enum():

    class Op(Enum):
        And=Enum.Auto()
        Or=Enum.Auto()

    @family_closure
    def PE_fc(family):
        @family.assemble(locals(), globals())
        class PE_Enum(Peak):
            def __call__(self, op: Const(Op), in0: Bit, in1: Bit) -> Bit:
                if op == Op.And:
                    return in0 & in1
                else: #op == Op.Or
                    return in0 | in1

        return PE_Enum

    # verify BV works
    PE_bv = PE_fc(family.PyFamily())
    vals = [Bit(0), Bit(1)]
    for op in Op.enumerate():
        for i0, i1 in itertools.product(vals, vals):
            res = PE_bv()(op, i0, i1)
            gold = (i0 & i1 ) if (op is Op.And) else (i0 | i1)
            assert res == gold

    # verify BV works
    PE_smt  = PE_fc(family.SMTFamily())
    Op_aadt = AssembledADT[Op, Assembler, SMTBitVector]
    vals = [SMTBit(0), SMTBit(1), SMTBit(), SMTBit()]
    for op in Op.enumerate():
        op = Op_aadt(op)
        for i0, i1 in itertools.product(vals, vals):
            res = PE_smt()(op, i0, i1)
            gold = (i0 & i1 ) if (op is Op.And) else (i0 | i1)
            assert res == gold

    # verify magma works
    asm = Assembler(Op)
    PE_magma = PE_fc(family.MagmaFamily())
    tester = fault.Tester(PE_magma)
    vals = [0, 1]
    for op in (Op.And, Op.Or):
        for i0, i1 in itertools.product(vals, vals):
            gold = (i0 & i1 ) if (op is Op.And) else (i0 | i1)
            tester.circuit.op = int(asm.assemble(op))
            tester.circuit.in0 = i0
            tester.circuit.in1 = i1
            tester.eval()
            tester.circuit.O.expect(gold)
    tester.compile_and_run("verilator", flags=["-Wno-fatal"])


def test_sum():
    Data = BitVector[16]
    class Op(Enum):
        Add = Enum.Auto()
        Or = Enum.Auto()

    class ImmOp(Product):
        opcode = Op
        imm = Data


    class Inst(Sum[ImmOp, Op]): pass

    @family_closure
    def PE_fc(family):
        @family.assemble(locals(), globals())
        class PE_Sum(Peak):
            def __call__(self, op: Const(Inst), in0: Data, in1: Data) -> Data:
                imm = family.BitVector[16](0)
                if op[ImmOp].match:
                    imm = op[ImmOp].value.imm
                    op = op[ImmOp].value.opcode
                else:
                    op = op[Op].value

                if op == Op.Add:
                    r = in0 + in1 + imm
                else:
                    r = in0 | in1 | imm

                return r
        return PE_Sum


    # generate golds
    PE_bv = PE_fc(family.PyFamily())()

    golds = []
    for _ in range(N_TESTS):

        if random.randint(0, 1):
            op = Op.Add
        else:
            op = Op.Or

        if random.randint(0, 1):
            imm = BitVector.random(16)
            inst = Inst(ImmOp(op, imm))
        else:
            inst = Inst(op)

        in0 = BitVector.random(16)
        in1 = BitVector.random(16)
        out = PE_bv(inst, in0, in1)
        golds.append((inst, in0, in1, out))

    # verify smt works
    PE_smt  = PE_fc(family.SMTFamily())
    Inst_aadt = AssembledADT[Inst, Assembler, SMTBitVector]

    def to_smt(v):
        return SMTBitVector[16](v.value)

    for inst, in0, in1, out in golds:
        inst = Inst_aadt(inst)
        res = PE_smt()(inst, to_smt(in0), to_smt(in1))
        assert res == out

    # verify magma works
    asm = Assembler(Inst)
    PE_magma = PE_fc(family.MagmaFamily())
    tester = fault.Tester(PE_magma)
    for inst, in0, in1, out in golds:
        tester.circuit.op = int(asm.assemble(inst))
        tester.circuit.in0 = in0
        tester.circuit.in1 = in1
        tester.eval()
        tester.circuit.O.expect(out)
    tester.compile_and_run("verilator", flags=["-Wno-fatal"])



def test_wrap_with_disassembler():
    class HashableDict(dict):
        def __hash__(self):
            return hash(tuple(sorted(self.keys())))

    PE_magma = PE_fc(family.MagmaFamily())
    instr_type = PE_fc(family.PyFamily()).input_t.field_dict['inst']
    asm = Assembler(instr_type)
    instr_magma_type = type(PE_magma.interface.ports['inst'])
    PE_wrapped = wrap_with_disassembler(
        PE_magma,
        asm.disassemble,
        asm.width,
        HashableDict(asm.layout),
        instr_magma_type
    )



def test_composition():
    PE_magma = PE_fc(family.MagmaFamily())
    PE_py = PE_fc(family.PyFamily())()
    tester = fault.Tester(PE_magma)
    Op = Inst.op0
    assert Op is Inst.op1
    asm = Assembler(Inst)
    for op0, op1, choice, in0, in1 in itertools.product(
            Inst.op0.enumerate(),
            Inst.op1.enumerate(),
            (Bit(0), Bit(1)),
            range(4),
            range(4),
        ):
        in0 = BitVector[16](in0)
        in1 = BitVector[16](in1)
        inst =Inst(op0=op0, op1=op1, choice=choice)
        gold = PE_py(inst=inst, data0=in0, data1=in1)

        tester.circuit.inst = asm.assemble(inst)
        tester.circuit.data0 = in0
        tester.circuit.data1 = in1
        tester.eval()
        tester.circuit.O.expect(gold)
    tester.compile_and_run("verilator", flags=["-Wno-fatal"])


def test_register():
    @family_closure
    def PE_fc(family):
        Reg = family.gen_register(family.BitVector[8], 0)
        @family.assemble(locals(), globals())
        class CounterPe(Peak):
            def __init__(self):
                self.register: Reg = Reg()

            def __call__(self, en: Bit) -> BitVector[8]:
                val = self.register.prev()
                self.register(val+1, en)
                return val

        return CounterPe

    PE_magma = PE_fc(family.MagmaFamily())
    PE_py = PE_fc(family.PyFamily())()
    tester = fault.Tester(PE_magma, PE_magma.CLK)

    for en in BitVector.random(32):
        gold = PE_py(en)
        tester.circuit.en = en
        tester.circuit.O.expect(gold)
        tester.step(2)
    tester.compile_and_run("verilator", flags=["-Wno-fatal"])
