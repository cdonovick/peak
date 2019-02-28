import pytest
from peak.adt import Product, Sum, Enum, Tuple

class En(Enum):
    a = 0
    b = 1

class Pr(Product):
    x:En
    y:En

Su = Sum[En, Pr]

Tu = Tuple[En, En]

def test_enum():
    assert set(En.enumerate()) == {
            En.a,
            En.b,
    }

    assert En.a.value == 0
    assert En.a == En(0)

    assert issubclass(En, Enum)
    assert isinstance(En.a, Enum)
    assert isinstance(En.a, En)

def test_product():
    assert set(Pr.enumerate()) == {
            Pr(En.a, En.a),
            Pr(En.a, En.b),
            Pr(En.b, En.a),
            Pr(En.b, En.b),
    }

    assert Pr(En.a, En.a).value == (En.a, En.a)

    assert issubclass(Pr, Product)
    assert isinstance(Pr(En.a, En.a), Product)
    assert isinstance(Pr(En.a, En.a), Pr)

    assert Pr(En.a, En.b).y == En.b
    with pytest.raises(TypeError):
        Pr(En.a, 1)


def test_sum():
    assert set(Su.enumerate()) == {
            Su(En.a),
            Su(En.b),
            Su(Pr(En.a, En.a)),
            Su(Pr(En.a, En.b)),
            Su(Pr(En.b, En.a)),
            Su(Pr(En.b, En.b)),
    }

    assert Su(En.a).value == En.a

    assert issubclass(Su, Sum)
    assert isinstance(Su(En.a), Su)
    assert isinstance(Su(En.a), Sum)

    with pytest.raises(TypeError):
        Su(1)

def test_tuple():
    assert set(Tu.enumerate()) == {
            Tu(En.a, En.a),
            Tu(En.a, En.b),
            Tu(En.b, En.a),
            Tu(En.b, En.b),
    }

    assert Tu(En.a, En.a).value == (En.a, En.a)

    assert issubclass(Tu, Tuple)
    assert isinstance(Tu(En.a, En.a), Tuple)
    assert isinstance(Tu(En.a, En.a), Tu)

    assert Tu(En.a, En.b)[1] == En.b

    with pytest.raises(TypeError):
        Tu(En.a, 1)
