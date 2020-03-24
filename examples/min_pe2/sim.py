from hwtypes import Tuple

from .isa import ISA_fc
from peak import Peak, name_outputs, family_closure, assemble

@family_closure
def PE_fc(family):
    Word, Bit, Inst  = ISA_fc(family)
    T = Tuple[Word, Bit]
    UInt = family.Unsigned
    UData = UInt[16]


    @assemble(family, locals(), globals())
    class PE(Peak):

        @name_outputs(out=Word)
        def __call__(self, inst: Inst) -> Word:
            o0 = inst.operand_0
            if inst.operand_1[Word].match:
                # arith op
                o1 = inst.operand_1[Word].value
                if inst.Opcode == Inst.Opcode.A:
                    return UData(o0).adc(UData(o1), Bit(0))
                else:
                    return UData(o0).adc(UData(o1), Bit(1))
            else:
                # bit op
                ox = inst.operand_1[T].value
                o1 = ox[0]
                b  = ox[1]
                if inst.Opcode == Inst.Opcode.A:
                    res = o0 & o1
                else:
                    res = o0 | o1
                return b.ite(~res, res)
    return PE

