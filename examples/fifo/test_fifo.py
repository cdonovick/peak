import random
import pytest
import examples.fifo.asm as asm
from examples.fifo.isa import Word
from examples.fifo.sim import gen_fifo

LOGN = 2
N = 1 << LOGN

FIFO = gen_fifo(Word, LOGN)

def random_fifo(fifo, n, min=0, max=N):
    enqueue = asm.enqueue(Word(0))
    dequeue = asm.dequeue()
    while True:
        if fifo.fill() < max:
            fifo( asm.enqueue(Word(random.randint(0,15))) )
        elif fifo.fill() > min:
            fifo( asm.dequeue() )
        assert 0 <= int(fifo.full()) <= N
        if fifo.fill() == N:
            assert fifo.full()
        if fifo.fill() == 0:
            assert fifo.empty()
        if fifo.fill() == n:
            break
    

def test_nop():
    fifo = FIFO()
    assert fifo.empty()
    assert not fifo.full()
    fifo(asm.nop())
    assert fifo.empty()
    assert not fifo.full()

def test_enqueue():
    fifo = FIFO()
    assert fifo.empty()
    for i in range(N):
        assert not fifo.full()
        fifo(asm.enqueue(Word(i)))
        assert not fifo.empty()
    assert fifo.full()
    fifo(asm.enqueue(Word(0)))
    assert fifo.full()

def test_dequeue():
    fifo = FIFO()
    for i in range(20):
        assert fifo.empty()
        data_in = Word(i)
        fifo(asm.enqueue(Word(i)))
        data_out = fifo(asm.dequeue())
        assert data_in == data_out
    assert fifo.empty()

def test_full():
    fifo = FIFO()
    random_fifo(fifo, N, 0, N)
    assert fifo.full()

def test_two():
    fifo = FIFO()
    n = random.randint(0,N-2)
    random_fifo(fifo, n)
    fifo(asm.enqueue(Word(1)))
    fifo(asm.enqueue(Word(2)))
    random_fifo(fifo, n+2, n, n+2)
    assert fifo(asm.dequeue()) == Word(1)
    assert fifo(asm.dequeue()) == Word(2)


# test simulataneous Enqueue, Dequeue
