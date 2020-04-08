import pytest

from peak import Peak, family_closure
from peak.assembler import Assembler, AssembledADT
from peak.rtl_utils import wrap_with_disassembler
from peak import family
from hwtypes import Bit, SMTBit, SMTBitVector, BitVector, Enum
from examples.demo_pes.pe6 import PE_fc
from examples.demo_pes.pe6.sim import Inst

import fault
import magma
import itertools

def test_assemble():
    @family_closure
    def PE_fc(family):
        Bit = family.Bit

        @family.assemble(locals(), globals())
        class PESimple(Peak, typecheck=True):
            def __call__(self, in0: Bit, in1: Bit) -> Bit:
                return in0 & in1

        return PESimple

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
    tester = fault.Tester(PE_magma)
    vals = [0, 1]
    for i0, i1 in itertools.product(vals, vals):
        tester.circuit.in0 = i0
        tester.circuit.in1 = i1
        tester.eval()
        tester.circuit.O.expect(i0 & i1)
    tester.compile_and_run("verilator", flags=["-Wno-fatal"])


def test_enum():

    class Op(Enum):
        And=1
        Or=2

    @family_closure
    def PE_fc(family):

        Bit = family.Bit
        @family.assemble(locals(), globals())
        class PE_Enum(Peak):
            def __call__(self, op: Op, in0: Bit, in1: Bit) -> Bit:
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

