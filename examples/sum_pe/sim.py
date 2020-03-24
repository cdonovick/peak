from hwtypes import Tuple

from .isa import ISA_fc
from peak import Peak, name_outputs, family_closure, assemble, Const


@family_closure
def PE_fc(family):
    Inst, Operand0T, Operand1T, Word, T = ISA_fc(family)

    @assemble(family, locals(), globals())
    class PE(Peak):

        @name_outputs(out=Word)
        def __call__(self, inst: Const(Inst), op0: Operand0T, op1: Operand1T) -> Word:
            o0 = op0
            if op1[Word].match:
                # arith op
                o1 = op1[Word].value
                if inst.Opcode == Inst.Opcode.A:
                    return o0 + o1 + inst.offset
                else:
                    return o0 - o1 + inst.offset
            else:
                # bit op
                ox = op1[T].value
                o1 = ox[0]
                b  = ox[1]
                if inst.Opcode == Inst.Opcode.A:
                    res = o0 & o1
                else:
                    res = o0 | o1
                return b.ite(~res, res)
    return PE

