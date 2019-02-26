from peak.adt import Product, Sum, Enum, product

class En(Enum):
    a = 0
    b = 1

@product
class Pr(Product):
    x:En
    y:En

Su = Sum[En, Pr]

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

