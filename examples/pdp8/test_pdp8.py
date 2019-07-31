import random
from collections import namedtuple
from examples.pdp8 import PDP8, Word
import examples.pdp8.isa as isa
import examples.pdp8.asm as asm
import pytest

NVALUES = 16
def random12():
    return random.randint(0,1<<12-1)
testvectors1 = [random12() for i in range(NVALUES)]
testvectors2 = [(random12(), random12()) for i in range(NVALUES)]

@pytest.mark.parametrize("ab", testvectors2)
def test_and(ab):
    inst = asm.and_(1)
    pdp8 = PDP8([inst,Word(ab[0])])
    pdp8.poke_acc(ab[1])
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == ab[0]&ab[1]

@pytest.mark.parametrize("ab", testvectors2)
def test_tad(ab):
    pdp8 = PDP8([asm.tad(1),Word(ab[0])])
    pdp8.poke_acc(ab[1])
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == ab[0]+ab[1]

def test_dca():
    pdp8 = PDP8([asm.dca(1)])
    pdp8.poke_mem(1,0)
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 0
    assert pdp8.peak_mem(1) == 1

def test_isz():
    pdp8 = PDP8([asm.isz(1)])
    pdp8.poke_mem(1,0)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 0
    assert pdp8.peak_mem(1) == 1


def test_jmp():
    pdp8 = PDP8([asm.jmp(2)])
    pdp8()
    assert pdp8.peak_pc() == 2

def test_cla():
    pdp8 = PDP8([asm.cla()])
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_acc() == 0

def test_sna():
    pdp8 = PDP8([asm.sna()])
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_pc() == 2
