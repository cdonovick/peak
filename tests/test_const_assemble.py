from peak import family_closure, Peak, Const
import pytest

def test_Const_BV():

    @family_closure
    def fc(family):
        BV = family.BitVector
        Bit = family.Bit

        @family.assemble(locals(), globals())
        class P(Peak):
            def __call__(self, bv: Const(BV[2]), bit: Const(Bit)) -> Bit:
                return Bit(1)

        return P

    fc.Py
    fc.SMT
    pytest.skip("Magma currently broken")
    fc.Magma
