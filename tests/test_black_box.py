#import pytest

from hwtypes import Bit, BitVector

from peak import Const, family_closure, Peak, name_outputs
from peak.family import BlackBox
from peak.family import SMTFamily, PyFamily
#from peak.mapper import ArchMapper, RewriteRule

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
    pe_py.BB1._set_outputs(b[1])
    pe_py.BB2._set_outputs(b[2])
    pe_py.BB3._set_outputs(b[3])

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
        v = pe_py(BV[2](i), x)
        check(v==out)
        check_BB_inputs()

def test_black_box_smt():

    SBV = SMTFamily().BitVector
    b = [SBV[8](name=f"b{i}") for i in range(4)]
    x = SBV[8](name='x')
    pe_smt = PE_fc.SMT()
    pe_smt.BB1._set_outputs(b[1])
    pe_smt.BB2._set_outputs(b[2])
    pe_smt.BB3._set_outputs(b[3])

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
        v = pe_smt(SBV[2](i), x)
        check(v==out)
        check_BB_inputs()






