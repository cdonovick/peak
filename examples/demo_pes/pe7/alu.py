from .isa import Op
from peak import Peak, assemble, family_closure

@family_closure
def ALU_fc(family):
    Bit = family.Bit
    Data = family.BitVector[16]
    SData = family.Signed[16]

    @assemble(family, locals(), globals())
    class ALU(Peak):
        def __call__(self, inst : Op, data0 : Data, data1 : Data) -> Data:
            data0, data1 = SData(data0), SData(data1)
            if inst == Op.Add:
                res = data0 + data1
            else:
                res = data0 & data1

            return res

    return ALU
