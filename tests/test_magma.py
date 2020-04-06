from peak import Peak, family_closure, assemble
from peak.assembler import Assembler, AssembledADT, MagmaADT
from peak.rtl_utils import wrap_with_disassembler
from hwtypes import Bit, SMTBit, SMTBitVector, BitVector, Enum, Tuple
from examples.demo_pes.pe6 import PE_fc
import ast_tools
from ast_tools.passes import begin_rewrite, end_rewrite, loop_unroll
from examples.demo_pes.pe6.sim import Inst

import fault
import magma
import itertools

def test_assemble():
    @family_closure
    def PE_fc(family):
        Bit = family.Bit

        @assemble(family, locals(), globals())
        class PESimple(Peak, typecheck=True):
            def __call__(self, in0: Bit, in1: Bit) -> Bit:
                return in0 & in1

        return PESimple

    #verify BV works
    PE_bv = PE_fc(Bit.get_family())
    vals = [Bit(0), Bit(1)]
    for i0, i1 in itertools.product(vals, vals):
        assert PE_bv()(i0, i1) == i0 & i1

    #verify SMT works
    PE_smt = PE_fc(SMTBit.get_family())
    vals = [SMTBit(0), SMTBit(1), SMTBit(), SMTBit()]
    for i0, i1 in itertools.product(vals, vals):
        assert PE_smt()(i0, i1) == i0 & i1

    #verify magma works
    PE_magma = PE_fc(magma.get_family())
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
        @assemble(family, locals(), globals())
        class PE_Enum(Peak):
            def __call__(self, op: Op, in0: Bit, in1: Bit) -> Bit:
                if op == Op.And:
                    return in0 & in1
                else: #op == Op.Or
                    return in0 | in1

        return PE_Enum

    # verify BV works
    PE_bv = PE_fc(Bit.get_family())
    vals = [Bit(0), Bit(1)]
    for op in Op.enumerate():
        for i0, i1 in itertools.product(vals, vals):
            res = PE_bv()(op, i0, i1)
            gold = (i0 & i1 ) if (op is Op.And) else (i0 | i1)
            assert res == gold

    # verify BV works
    PE_smt  = PE_fc(SMTBit.get_family())
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
    PE_magma = PE_fc(magma.get_family())
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

    PE_magma = PE_fc(magma.get_family())
    instr_type = PE_fc(Bit.get_family()).input_t.field_dict['inst']
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
    PE_magma = PE_fc(magma.get_family())
    PE_py = PE_fc(BitVector.get_family())()
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

def test_magma_bug():

    OutT =magma.Tuple[magma.Bit, magma.Bit]
    @magma.circuit.combinational
    def PEGold(in0: magma.Bit) -> OutT:
        return OutT(in0, in0)

    @family_closure
    def PEbug_fc(family):
        Bit = family.Bit
        OutT = Tuple[Bit, Bit]
        @assemble(family, locals(), globals())
        class PEbug(Peak):
            def __call__(self, in0: Bit) -> OutT:
                assert 0
                return OutT(in0, in0)

        return PEBug

    PE_magma = PEbug_fc(magma.get_family())

def test_magma2_bug():

    InT =magma.Tuple[magma.Bit, magma.Bit]
    @magma.circuit.combinational
    def PEGold(in_: InT) -> magma.Bit:
        return InT[0]

    @family_closure
    def PEbug_fc(family):
        Bit = family.Bit
        InT = Tuple[Bit, Bit]
        @assemble(family, locals(), globals())
        class PEbug(Peak):
            def __call__(self, in_: InT) -> Bit:
                return in_[0]

        return PEbug

    PE_magma = PEbug_fc(magma.get_family())


def test_tuple():
    def gen(num_outputs):
        @family_closure
        def PE_fc(family):
            Bit = family.Bit
            OutT = Tuple[(Bit for _ in range(num_outputs))]
            if family is not magma.get_family():
                OutT = AssembledADT[OutT, Assembler, family.BitVector]
                constructor = OutT.from_fields
            else:
                #OutT = MagmaADT[OutT, Assembler, magma.Bits, magma.Direction.Undirected]
                constructor = OutT
            @assemble(family, locals(), globals())
            class PETuple(Peak):
                @end_rewrite()
                @loop_unroll()
                @begin_rewrite()
                def __call__(self, in0: Bit, in1: Bit) -> OutT:
                    ret = in0 & in1
                    outputs = []
                    for _ in ast_tools.macros.unroll(range(num_outputs)):
                        outputs.append(ret)
                    return constructor(*outputs)

            return PETuple
        return PE_fc

    PE_fc = gen(2)

    #verify BV works
    PE_bv = PE_fc(Bit.get_family())
    vals = [Bit(0), Bit(1)]
    for i0, i1 in itertools.product(vals, vals):
        ret = PE_bv()(i0, i1)
        assert ret[0] == i0 & i1

    #verify SMT works
    PE_smt = PE_fc(SMTBit.get_family())
    vals = [SMTBit(0), SMTBit(1), SMTBit(), SMTBit()]
    for i0, i1 in itertools.product(vals, vals):
        assert PE_smt()(i0, i1)[0] == i0 & i1

    #verify magma works
    PE_magma = PE_fc(magma.get_family())
    print(PE_magma)
    tester = fault.Tester(PE_magma)
    vals = [0, 1]
    for i0, i1 in itertools.product(vals, vals):
        ret = i0 & i1
        tester.circuit.in0 = i0
        tester.circuit.in1 = i1
        tester.eval()
        tester.circuit.O.expect((ret<<1)| ret )
    tester.compile_and_run("verilator", flags=["-Wno-fatal"])



