from .isa import Op
from peak import Peak, family_closure

@family_closure
def ALU_fc(family):
    Bit = family.Bit
    Data = family.BitVector[16]
    SData = family.Signed[16]

    @family.assemble(locals(), globals())
    class ALU(Peak):
        def __call__(self, inst : Op, data0 : Data, data1 : Data) -> Data:
            data0, data1 = SData(data0), SData(data1)
            if inst == Op.Add:
                res = data0 + data1
            elif inst == Op.And:
                res = data0 & data1
            elif inst == Op.Xor:
                res = data0 ^ data1
            else: #inst == Op.Shft:
                res = data0.bvshl(data1)

            return res

    return ALU
