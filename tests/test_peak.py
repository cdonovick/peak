import pytest
from peak import *
from hwtypes.modifiers import new
from hwtypes import BitVector

@pytest.mark.parametrize("n", [4])
def test_bits(n):
    BitsN = new(BitVector, n)
    for i in range(1<<n):
        bits = BitsN(i)
        assert bits.as_uint() == i
