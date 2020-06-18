from hwtypes import Tuple

from .isa import ISA_fc
from peak import Peak, name_outputs, family_closure, Const


@family_closure
def PE_fc(family):
    isa = ISA_fc(family)
    @family.assemble(locals(), globals())
    class PE(Peak):

        @name_outputs(out=isa.Word)
        def __call__(self, inst: Const(isa.Inst), in0: isa.Word, in1: isa.Word, in2: isa.Word, in3: family.Bit) -> isa.Word:
            is_bitop = ~inst[isa.ArithOp].match
            if not is_bitop:
                arithOp = inst[isa.ArithOp].value
                op = arithOp[0]
                offset = arithOp[1]
                if op == isa.Op.A:
                    return in0 + in1 + offset
                else:
                    return in0 - in1 + offset
            else:
                # bit op
                bitOp = inst[isa.BitOp].value
                #op = bitOp.op
                #neg = bitOp.neg
                op = bitOp[0]
                neg = bitOp[1]
                if op == isa.Op.A:
                    res = in0 & in1
                else:
                    res = in0 | in1
                return neg.ite(~res, res)
    return PE

