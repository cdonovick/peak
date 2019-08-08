from isa import gen_isa
from hwtypes import Product, Sum, Enum, Tuple


def gen_sim(family):
    Word, Bit, Inst  = gen_isa(family)
    T = Tuple[Word, Bit]
    S = Sum[Word, T]

    def sim(inst: Inst):
        o0 = inst.operand_0
        op = inst.Opcode

        if inst.operand_1.match(Word):
            o1 = inst.operand_1[Word]
            if inst.Opcode == Inst.Opcode.A:
                return o0 ^ o1
            else:
                return o0 - o1
        else:
            ox = inst.operand_1[T]
            o1 = ox[0]
            b  = ox[1]
            if inst.Opcode == Inst.Opcode.A:
                res = o0 & o1
                return b.ite(~res, res)
            else:
                return o0.adc(o1, b)

    return Word, Bit, Inst, sim
