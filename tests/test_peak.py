import pytest
from peak import *

@pytest.mark.parametrize("n", [4])
def test_bits(n):
    BitsN = Bits(n)
    for i in range(1<<n):
        bits = BitsN(i)
        assert bits.as_uint() == i
