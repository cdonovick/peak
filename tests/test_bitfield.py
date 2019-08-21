from hwtypes.adt import Product, Sum, Enum
from hwtypes import Bit, BitVector
from peak.bitfield import encode, size, tag
import pytest

Byte = BitVector[8]

class En1(Enum):
    a = 0
    b = 1

class En2(Enum):
    c = 0
    d = 1

class Pr(Product):
    x = En1
    y = En2

Su = Sum[En1, En2]
tag({En1:0, En2:1})(Su)

Su2 = Sum[En1, Pr]
tag({En1:0, Pr:1})(Su2)

def test_bit():
    assert encode(Bit(0)) == 0
    assert encode(Bit(1)) == 1

def test_byte():
    assert encode(Byte(0)) == 0
    assert encode(Byte(1)) == 1

def test_enum():
    assert size(En1) == 1
    assert size(En2) == 1
    assert encode(En1(En1.a)) == 0
    assert encode(En1(En1.b)) == 1
    assert encode(En2(En2.c)) == 0
    assert encode(En2(En2.d)) == 1


def test_product():
    assert size(Pr) == 2
    assert set(Pr.enumerate()) == {
            Pr(En1.a, En2.c),
            Pr(En1.a, En2.d),
            Pr(En1.b, En2.c),
            Pr(En1.b, En2.d),
    }
    assert encode(Pr(En1.a, En2.c)) == 0
    assert encode(Pr(En1.b, En2.c)) == 1
    assert encode(Pr(En1.a, En2.d)) == 2
    assert encode(Pr(En1.b, En2.d)) == 3

def test_sum():
    assert size(Su) == 2
    assert encode(Su(En1.a)) == 0
    assert encode(Su(En1.b)) == 2
    assert encode(Su(En2.c)) == 1
    assert encode(Su(En2.d)) == 3

    assert size(Su2) == 3
    assert encode(Su2(En1.a)) == 0
    assert encode(Su2(Pr(En1.a,En2.c))) == 1


