from peak import Peak, family_closure, family
from peak.register import gen_Register3

@family_closure
def Mul_fc(family):
    Data = family.BitVector[16]
    Reg = gen_Register3(16)(family)
    @family.assemble(locals(), globals())
    class Mul(Peak):
        def __init__(self):
            self.out_reg: Reg = Reg()

        def __call__(self, a: Data, b: Data) -> Data:
            return self.out_reg(a*b)

    return Mul

@family_closure
def Add_fc(family):
    Data = family.BitVector[16]
    Reg = gen_Register3(16)(family)
    @family.assemble(locals(), globals())
    class Add(Peak):
        def __init__(self):
            self.out_reg: Reg = Reg()

        def __call__(self, a: Data, b: Data) -> Data:
            return self.out_reg(a+b)

    return Add

#Computes a*b +c with latency=2
@family_closure
def FMA_fc(family):
    Data = family.BitVector[16]

    Mul = Mul_fc(family)
    Add = Add_fc(family)
    Reg = gen_Register3(16)(family)
    @family.assemble(locals(), globals())
    class FMA(Peak):
        def __init__(self):
            self.mul: Mul = Mul()
            self.add: Add = Add()
            self.c_reg: Reg = Reg()

        def __call__(self, a: Data, b: Data, c: Data) -> Data:
            mul_out = self.mul(a, b)
            c_delayed = self.c_reg(c)
            return self.add(mul_out, c_delayed)

    return FMA

def test_FMA():
    Data = family.PyFamily().BitVector[16]
    fma = (FMA_fc.Py)()

    #Assume state has already been updated (or set by test)
    out0 = fma(a=Data(3), b=Data(5), c=Data(7))
    assert out0 == Data(0)
    assert fma.c_reg.get() == Data(0)
    fma.update_state()
    assert fma.c_reg.get() == Data(7)
    out1 = fma(a=Data(0), b=Data(0), c=Data(0))
    assert out1 == Data(0)
    assert fma.c_reg.get() == Data(7)
    fma.update_state()
    assert fma.c_reg.get() == Data(0)
    out2 = fma(a=Data(0), b=Data(0), c=Data(0))
    assert out2 == Data(3*5+7)
    fma.update_state()
    fma.c_reg.set(Data(13))
    out3 = fma(a=Data(0), b=Data(0), c=Data(0))
    assert out3 == Data(0)
    assert fma.add.out_reg.get() == Data(0)
    fma.update_state()
    assert fma.add.out_reg.get() == Data(13)

