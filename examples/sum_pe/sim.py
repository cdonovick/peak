from hwtypes import Tuple

from .isa import ISA_fc
from peak import Peak, name_outputs, family_closure, Const


@family_closure
def PE_fc(family):
    isa = ISA_fc.Py
    @family.assemble(locals(), globals())
    class PE(Peak):

        @name_outputs(out=isa.Word, out_bit=isa.Bit)
        def __call__(self, inst: Const(isa.Inst), in0: isa.Word, in1: isa.Word, in2: isa.Word, in3: family.Bit) -> (isa.Word, isa.Bit):
            is_bitop = ~inst[isa.ArithOp].match
            if not is_bitop:
                arithOp = inst[isa.ArithOp].value
                op = arithOp[0]
                offset = arithOp[1]
                if op == isa.Op.A:
                    return in0 + in1 + offset, in3
                else:
                    return in0 - in1 + offset, in3
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
                return neg.ite(~res, res), in3
    return PE

