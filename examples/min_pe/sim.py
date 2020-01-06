from .isa import ISA_fc
from hwtypes import Product, Sum, Enum, Tuple, SMTBit
from peak import Peak, name_outputs, family_closure, update_peak

@family_closure
def PE_fc(family):
    Word, Bit, Inst  = ISA_fc(family)
    T = Tuple[Word, Bit]
    class PE(Peak):

        @name_outputs(out=Word)
        def __call__(self, inst: Inst):
            o0 = inst.operand_0
            if inst.operand_1[Word].match:
                # arith op
                o1 = inst.operand_1[Word].value
                if inst.Opcode == Inst.Opcode.A:
                    return o0 + o1
                else:
                    return o0 - o1
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

    return update_peak(PE, family)
