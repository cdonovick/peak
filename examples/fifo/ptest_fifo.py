import pytest
from .fifo import FIFO

LOGN = 4
N = 1 << LOGN

def test_init():
    fifo = FIFO(LOGN)
    assert fifo.empty()
    assert not fifo.full()

def test_full():
    fifo = FIFO(LOGN)
    assert fifo.empty()
    assert not fifo.full()
    for i in range(N):
        fifo.write(i)
        assert not fifo.empty()
    assert fifo.full()
