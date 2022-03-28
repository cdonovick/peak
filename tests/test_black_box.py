from hwtypes import Bit, BitVector, Product, Enum
from peak import Const, family_closure, Peak
from peak.family import PyFamily
from peak.float import float_lib_gen, RoudningMode_utils, RoundingMode
import examples.fp_pe as fp
from hwtypes import SMTBitVector as SBV, SMTBit as SBit
from peak.family import SMTFamily
from peak.black_box import BlackBox, get_black_boxes, get_black_box

@family_closure
def BB_fc(family):
    Data = BitVector[8]

    @family.assemble(locals(), globals())
    class BB(Peak, BlackBox):
        def __call__(self, x: Data) -> Data:
            return family.BitVector[8](0)

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
                return b1
            elif instr == 2:
                return b2
            else:
                return b3

    return PE

def test_black_box_py():

    BV = PyFamily().BitVector
    x = BV[8](13)
    pe_py = PE_fc.Py()

    for i, out in enumerate((
        x+5,
        0,
        0,
        -1
    )):
        v = pe_py(BV[2](i), x)
        assert v==out

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


def test_float_const_rm_magma():
    fplib = float_lib_gen(7, 8)
    @family_closure
    def arch_fc(family):
        Data = BitVector[16]
        class Inst(Product):
            class Op(Enum):
                add = 1
                fpadd = 2
                fpmul = 2

        Add = fplib.const_rm(RoundingMode.RNE).Add_fc(family)
        Mul = fplib.const_rm(RoundingMode.RNE).Mul_fc(family)

        @family.assemble(locals(), globals())
        class Arch(Peak):
            def __init__(self):
                self.fpadd: Add = Add()
                self.fpmul: Mul = Mul()

            def __call__(self, inst: Const(Inst), a: Data, b: Data) -> Data:
                fpadd = self.fpadd(a, b)
                if inst.Op == Inst.Op.add:
                    return a + b
                else: #inst == Inst.OP.fpadd_
                    return fpadd
        return Arch
    m = arch_fc.Magma


#Test the floating point libs
def test_float():
    fplib = float_lib_gen(3, 4)
    add_obj = fplib.Add_fc.Py()
    paths_to_bbs = get_black_boxes(add_obj)
    assert paths_to_bbs == {():add_obj}

def test_fp_pe_bb():
    PE = fp.PE_fc.Py
    pe = PE()
    paths_to_bbs = get_black_boxes(pe)
    for path in (
        ("FPU", "add"),
        ("FPU", "mul"),
        ("FPU", "sqrt"),
    ):
        assert path in paths_to_bbs
        bb_inst = paths_to_bbs[path]
        assert bb_inst is get_black_box(pe, path)
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
    paths_to_bbs = get_black_boxes(pe)
    for bb in paths_to_bbs.values():
        bb._set_outputs(SBV[16]())
    val = pe(inst, SBV[16](name='a'), SBV[16](2))
    for bb in paths_to_bbs.values():
        bb_inputs = bb._get_inputs()




