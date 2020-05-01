from peak import Peak, family_closure
from peak import family as f
from hwtypes.adt import Enum, Tuple, Product, Sum

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

def test_Product():
    @family_closure
    def PE_fc(family):
        Bit = family.Bit
        BV = family.BitVector
        T = Tuple[Bit, Bit]
        class P(Product):
            a = T
            b = BV[3]

        Tc = family.get_constructor(T)
        Pc = family.get_constructor(P)
        @family.assemble(locals(), globals())
        class PEProduct(Peak):
            def __call__(self, in0: Bit, in1: Bit) -> (P, T, Bit):
                tup = Tc(~in1, in0)
                if tup[0]:
                    b = BV[3](3)
                else:
                    b = BV[3](1)
                p = Pc(a=tup, b=b)
                if p.b[2]:
                    return p, p.a, in0
                else:
                    return p, tup, in1

        return PEProduct

    check_families(PE_fc)

def test_Sum():
    class E(Enum):
        a=1
        b=2
    @family_closure
    def PE_fc(family):
        Bit = family.Bit
        T = Tuple[Bit, Bit]
        S = Sum[E, T]
        Ec = family.get_constructor(E)
        Tc = family.get_constructor(T)
        Sc = family.get_constructor(S)
        @family.assemble(locals(), globals())
        class PESum(Peak):
            def __call__(self, in0: Bit, in1: Bit) -> S:
                if in0:
                    tup = Tc(~in1, in0)
                    s = Sc(T, tup)
                else:
                    s = Sc(E, Ec(E.a))
                return s
        return PESum

    check_families(PE_fc)

