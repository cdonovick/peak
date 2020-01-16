from hwtypes.adt import Product, Sum, Enum
from hwtypes import Bit, BitVector
from peak.bitfield import encode, sumsize, size, tag, bitfield
import pytest

class En1(Enum):
    a = 0
    b = 1

class En2(Enum):
    c = 0
    d = 1

class Pr(Product):
    x = En1
    y = En2

def test_bit():
    assert encode(Bit(0)) == 0
    assert encode(Bit(1)) == 1

    bitfield(2)(Bit)
    assert encode(Bit(1)) == 4

def test_byte():
    Byte = BitVector[8]
    assert encode(Byte(0)) == 0
    assert encode(Byte(1)) == 1

    bitfield(2)(BitVector[8])
    assert encode(Byte(1)) == 4

def test_enum():
    assert size(En1) == 1
    assert size(En2) == 1
    assert encode(En1(En1.a)) == 0
    assert encode(En1(En1.b)) == 1
    assert encode(En2(En2.c)) == 0
    assert encode(En2(En2.d)) == 1

    @bitfield(2)
    class E(Enum):
        a = 0
        b = 1
    assert encode(E(E.a)) == 0
    assert encode(E(E.b)) == 4


def test_product():
    assert size(Pr) == 2
    assert set(Pr.enumerate()) == {
            Pr(En1.a, En2.c),
            Pr(En1.a, En2.d),
            Pr(En1.b, En2.c),
            Pr(En1.b, En2.d),
    }
    s = size(En1)
    assert encode(Pr(En1.a, En2.c)) == (encode(En2.c) << s) | encode(En1.a)
    assert encode(Pr(En1.b, En2.c)) == (encode(En2.c) << s) | encode(En1.b)
    assert encode(Pr(En1.a, En2.d)) == (encode(En2.d) << s) | encode(En1.a)
    assert encode(Pr(En1.b, En2.d)) == (encode(En2.d) << s) | encode(En1.b)

    s = size(En2)
    assert encode(Pr(En1.a, En2.c), reverse=True) == (encode(En1.a) << s) | encode(En2.c)
    assert encode(Pr(En1.b, En2.c), reverse=True) == (encode(En1.b) << s) | encode(En2.c)
    assert encode(Pr(En1.a, En2.d), reverse=True) == (encode(En1.a) << s) | encode(En2.d)
    assert encode(Pr(En1.b, En2.d), reverse=True) == (encode(En1.b) << s) | encode(En2.d)

def test_sum():
    Su = Sum[En1, En2]
    tag({En1:0, En2:1})(Su)

    assert size(Su) == 2
    s = sumsize(Su)
    assert encode(Su(En1.a)) == Su.tags[En1] | (encode(En1.a) << s)
    assert encode(Su(En1.b)) == Su.tags[En1] | (encode(En1.b) << s)
    assert encode(Su(En2.c)) == Su.tags[En2] | (encode(En2.c) << s)
    assert encode(Su(En2.d)) == Su.tags[En2] | (encode(En2.d) << s)

    s = size(Su) - sumsize(Su)
    assert encode(Su(En1.a), reverse=True) == encode(En1.a) | (Su.tags[En1] << s)
    assert encode(Su(En1.b), reverse=True) == encode(En1.b) | (Su.tags[En1] << s)
    assert encode(Su(En2.c), reverse=True) == encode(En2.c) | (Su.tags[En2] << s)
    assert encode(Su(En2.d), reverse=True) == encode(En2.d) | (Su.tags[En2] << s)

    Su2 = Sum[En1, Pr]
    tag({En1:0, Pr:1})(Su2)

    assert size(Su2) == 3
    assert encode(Su2(En1.a)) == 0
    assert encode(Su2(Pr(En1.a,En2.c))) == 1

