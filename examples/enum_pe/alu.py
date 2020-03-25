from peak import Peak, name_outputs, family_closure, assemble
from hwtypes import Enum


class ALU_t(Enum):
    Add = 0
    Sub = 1
    Or = 2
    And = 3
    SHR = 4


class Signed_t(Enum):
    unsigned = 0
    signed = 1

@family_closure
def ALU_fc(family):

    Data = family.BitVector[16]
    Bit = family.Bit
    SData = family.Signed[16]
    UData = family.Unsigned[16]

    @assemble(family, locals(), globals())
    class ALU(Peak):
        @name_outputs(res=Data, res_p=Bit, Z=Bit, N=Bit, C=Bit, V=Bit)
        def __call__(self, alu: ALU_t, signed_: Signed_t, a: Data, b: Data) -> (Data, Bit, Bit, Bit, Bit, Bit):

            if signed_ == Signed_t.signed:
                a_s = SData(a)
                b_s = SData(b)
                shr = Data(a_s >> b_s)
            else: 
                a_u = UData(a)
                b_u = UData(b)
                shr = Data(a_u >> b_u)

            if (alu == ALU_t.Sub):
                b = ~b
                Cin = Bit(1)
            elif (alu == ALU_t.Add):
                Cin = Bit(0)  

            C = Bit(0)
            V = Bit(0)

            if (alu == ALU_t.Add) | (alu == ALU_t.Sub):
                res, C = UData(a).adc(UData(b), Cin)
                res_p = C
            elif alu == ALU_t.And:
                res, res_p = a & b, Bit(0)
            elif alu == ALU_t.Or:
                res, res_p = a | b, Bit(0)
            elif alu == ALU_t.SHR:
                res, res_p = shr, Bit(0)
            
            N = Bit(res[-1])
            Z = (res == 0)

            return res, res_p, Z, N, C, V

    return ALU
   