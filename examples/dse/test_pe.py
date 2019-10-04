from collections import namedtuple
import random
import pytest

from hwtypes.bit_vector import _Family_ as family
from .gen import gen_pe

Bit, Nibble, Word, Inst, ALU, Op, PE = gen_pe(1, 2, family)
WIDTH = 16

pe = PE()


def random_word():
    return Word(random.randint(0,1<<WIDTH-1))

NVALUES = 4
testvectors1 = [random_word() for i in range(NVALUES)]
testvectors2 = [random_word() for i in range(NVALUES)]

inst = namedtuple("inst", ["name", "func"])


@pytest.mark.parametrize("op", [
    inst(Op.And, lambda x, y: x&y),
    inst(Op.Add, lambda x, y: x+y),
    inst(Op.Mul, lambda x, y: x*y)
])
@pytest.mark.parametrize("a", testvectors1)
@pytest.mark.parametrize("b", testvectors2)
def test_pe(op, a,b):
    inst = Inst(alu = ALU(op.name, Nibble(0), Nibble(1)))
    res = pe(inst, [a, b])
    assert res == op.func(a,b)

