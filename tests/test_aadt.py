from peak import Peak, family_closure
from peak import family as f
from hwtypes.adt import Enum, Tuple

#Just verifies the compilation
def check_families(PE_fc):
    PE_bv = PE_fc(f.PyFamily())
    PE_smt = PE_fc(f.SMTFamily())
    PE_magma = PE_fc(f.MagmaFamily())

def test_Enum():

    class E(Enum):
        a=1
        b=2
    @family_closure
    def PE_fc(family):
        Bit = family.Bit
        Ec = family.get_constructor(E)
        print(Ec, type(Ec))
        @family.assemble(locals(), globals())
        class PEEnum(Peak, typecheck=True):
            def __call__(self, sel: Bit) -> E:
                if sel:
                    return Ec(E.a)
                else:
                    return Ec(E.b)

        return PEEnum

    check_families(PE_fc)

def test_Tuple():

    @family_closure
    def PE_fc(family):
        Bit = family.Bit
        T = Tuple[Bit, Bit]
        Tc = family.get_constructor(T)
        @family.assemble(locals(), globals())
        class PETuple(Peak):
            def __call__(self, in0: Bit, in1: Bit) -> (T, Bit):
                tup = Tc(~in1, in0)
                if in0:
                    res_bit = tup[0]
                else:
                    res_bit = tup[1]
                return tup, res_bit

        return PETuple

    check_families(PE_fc)

