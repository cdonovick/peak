from hwtypes import Bit, BitVector
from peak import Const, family_closure, Peak
from peak.family import PyFamily
from peak.float import Float
import examples.fp_pe as fp
from hwtypes import SMTBitVector as SBV, SMTBit as SBit
from peak.family import SMTFamily, BlackBox

@family_closure
def BB_fc(family):
    Data = BitVector[8]

    @family.assemble(locals(), globals())
    class BB(Peak, BlackBox):
        def __call__(self, x: Data) -> Data:
            ...

    return BB


@family_closure
def PE_fc(family):
    Data = BitVector[8]
    BB = BB_fc(family)

    @family.assemble(locals(), globals())
    class PE(Peak):
        def __init__(self):
            self.BB1: BB = BB()
            self.BB2: BB = BB()
            self.BB3: BB = BB()

        def __call__(self, instr: Const(BitVector[2]), in_: Data) -> Data:
            b1 = self.BB1(in_)
            b2 = self.BB2(~in_)
            b3 = ~(self.BB3(in_))
            if instr == 0:
                return in_ + 5
            elif instr == 1:
                return b1;
            elif instr == 2:
                return b2
            else:
                return b3

    return PE

def test_black_box_py():

    BV = PyFamily().BitVector
    b = [BV[8](i) for i in range(4)]
    x = BV[8](13)
    pe_py = PE_fc.Py()


    def check(v):
        assert v

    def check_BB_inputs():
        b1_in = pe_py.BB1._get_inputs()[0]
        b2_in = pe_py.BB2._get_inputs()[0]
        b3_in = pe_py.BB3._get_inputs()[0]
        check(b1_in == x)
        check(b2_in == ~x)
        check(b3_in == x)

    for i, out in enumerate((
        x+5,
        b[1],
        b[2],
        ~b[3]
    )):
        pe_py.BB1._set_outputs(b[1])
        pe_py.BB2._set_outputs(b[2])
        pe_py.BB3._set_outputs(b[3])
        v = pe_py(BV[2](i), x)
        check(v==out)
        check_BB_inputs()

def test_black_box_smt():

    SBV = SMTFamily().BitVector
    b = [SBV[8](name=f"b{i}") for i in range(4)]
    x = SBV[8](name='x')
    pe_smt = PE_fc.SMT()


    def check(v):
        assert v.value.is_constant()
        assert v.value.constant_value()

    def check_BB_inputs():
        b1_in = pe_smt.BB1._get_inputs()[0]
        b2_in = pe_smt.BB2._get_inputs()[0]
        b3_in = pe_smt.BB3._get_inputs()[0]
        check(b1_in == x)
        check(b2_in == ~x)
        check(b3_in == x)

    for i, out in enumerate((
        x+5,
        b[1],
        b[2],
        ~b[3]
    )):
        pe_smt.BB1._set_outputs(b[1])
        pe_smt.BB2._set_outputs(b[2])
        pe_smt.BB3._set_outputs(b[3])
        v = pe_smt(SBV[2](i), x)
        check(v==out)
        check_BB_inputs()



#Test the floating point libs
def test_float():
    fplib = Float(3, 4)
    add_obj = fplib.add_fc.Py()
    paths_to_bbs = BlackBox.get_black_boxes(add_obj)
    assert paths_to_bbs == {():add_obj}

def test_fp_pe_bb():
    PE = fp.PE_fc.Py
    pe = PE()
    paths_to_bbs = BlackBox.get_black_boxes(pe)
    for path in (
        ("FPU", "add"),
        ("FPU", "mul"),
        ("FPU", "sqrt"),
    ):
        assert path in paths_to_bbs
        bb_inst = paths_to_bbs[path]
        assert bb_inst is BlackBox.get_black_box(pe, path)
        assert isinstance(bb_inst, BlackBox)

def test_fp_pe_smt():
    pe = fp.PE_fc.SMT()
    AInst = SMTFamily().get_adt_t(fp.Inst)
    inst = AInst.from_fields(
        op=AInst.op(
            fpu=AInst.op.fpu(fp.FPU_op.FPAdd)
        ),
        imm=SBV[16](10),
        use_imm=SBit(name='ui')
    )
    paths_to_bbs = BlackBox.get_black_boxes(pe)
    for bb in paths_to_bbs.values():
        bb._set_outputs(SBV[16]())
    val = pe(inst, SBV[16](name='a'), SBV[16](2))
    for bb in paths_to_bbs.values():
        bb_inputs = bb._get_inputs()




