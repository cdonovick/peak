import random
import pytest
import hwtypes
from .import gen_fifo

# width of words in fifo
WIDTH = 32

# depth of fifo
LOG_DEPTH = 2
DEPTH = 1 << LOG_DEPTH

Word, Addr, asm, FIFO = gen_fifo(hwtypes.Bit.get_family(), WIDTH, DEPTH)

print(Word.size)
print(Addr.size)

# enqueue and dequeue until fifo has n elements in it
def random_fifo(fifo, n, min=0, max=DEPTH):
    #enqueue = asm.enqueue(Word(0))
    #dequeue = asm.dequeue()
    assert 0 <= n <= DEPTH
    while True:
        assert 0 <= int(fifo.fill()) <= DEPTH
        if fifo.fill() == n:
            break
        if fifo.full() == min:
            fifo( asm.enqueue(Word(random.randint(0,15))) )
        elif fifo.fill() == max:
            fifo( asm.dequeue() )
        else:
            if random.randint(0,1):
                fifo( asm.enqueue(Word(random.randint(0,15))) )
            else:
                fifo( asm.dequeue() )
        if fifo.fill() == DEPTH:
            assert fifo.full()
        if fifo.fill() == 0:
            assert fifo.empty()
    

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
    for i in range(DEPTH):
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
    random_fifo(fifo, DEPTH)
    assert fifo.full()

def test_two():
    fifo = FIFO()
    fifo(asm.enqueue(Word(1)))
    fifo(asm.enqueue(Word(2)))
    assert fifo(asm.dequeue()) == Word(1)
    assert fifo(asm.dequeue()) == Word(2)


# test simulataneous Enqueue, Dequeue
