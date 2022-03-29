import pytest

from peak import family
from peak import family_closure

class ExtendFamily:
    class MagmaFamily(family.MagmaFamily): pass
    class PyFamily(family.PyFamily): pass
    class SMTFamily(family.SMTFamily): pass
    class PyXFamily(family.PyXFamily): pass

@family_closure
def foo_fc(family): return family

@family_closure(ExtendFamily)
def bar_fc(family): return family


def test_bind():
    assert foo_fc.family is family
    assert bar_fc.family is ExtendFamily


@pytest.mark.parametrize('fc', [foo_fc, bar_fc])
def test_autocall(fc):
    # note that family closure just return their
    # arguments this shows fc.T calls fc(fc.family.TFamily())
    assert isinstance(fc.Magma, fc.family.MagmaFamily)
    assert isinstance(fc.Py, fc.family.PyFamily)
    assert isinstance(fc.SMT, fc.family.SMTFamily)
    assert isinstance(fc.PyX, fc.family.PyXFamily)
