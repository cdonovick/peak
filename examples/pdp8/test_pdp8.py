import random
from peak.bitfield import encode
from examples.pdp8 import PDP8, Word
import examples.pdp8.isa as isa
import examples.pdp8.asm as asm
import pytest

NVALUES = 4
def random12():
    return Word(random.randint(0,1<<12-1))
testvectors1 = [random12() for i in range(NVALUES)]
testvectors2 = [random12() for i in range(NVALUES)]

@pytest.mark.parametrize("a", testvectors1)
@pytest.mark.parametrize("b", testvectors2)
def test_and(a,b):
    addr = 1
    inst = asm.and_(addr)
    bits = encode(inst)
    assert bits == 0x020
    pdp8 = PDP8([inst])
    pdp8.poke_mem(addr,a)
    pdp8.poke_acc(b)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == a&b

@pytest.mark.parametrize("a", testvectors1)
@pytest.mark.parametrize("b", testvectors2)
def test_tad(a,b):
    addr = 1
    inst = asm.tad(addr)
    bits = encode(inst)
    assert bits == 0x21
    pdp8 = PDP8([inst])
    pdp8.poke_mem(addr,a)
    pdp8.poke_acc(b)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == a+b

def test_isz():
    addr = 1
    inst = asm.isz(addr)
    bits = encode(inst)
    assert bits == 0x22
    pdp8 = PDP8([inst])
    pdp8.poke_mem(addr,0)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 0
    assert pdp8.peak_mem(addr) == 1

@pytest.mark.parametrize("a", testvectors1)
def test_dca(a):
    addr = 1
    inst = asm.dca(addr)
    bits = encode(inst)
    assert bits == 0x23
    pdp8 = PDP8([inst])
    pdp8.poke_mem(addr,0)
    pdp8.poke_acc(a)
    pdp8()
    assert pdp8.peak_pc() == 1
    assert pdp8.peak_acc() == 0
    assert pdp8.peak_mem(addr) == a


def test_jms():
    addr = 2
    inst = asm.jms(addr)
    bits = encode(inst)
    assert bits == 0x44
    pdp8 = PDP8([inst])
    pdp8()
    assert pdp8.peak_pc() == 3
    assert pdp8.peak_acc() == 0
    assert pdp8.peak_mem(addr) == 1

def test_jmp():
    addr = 2
    inst = asm.jmp(addr)
    bits = encode(inst)
    assert bits == 0x45
    pdp8 = PDP8([inst])
    pdp8()
    assert pdp8.peak_pc() == addr

@pytest.mark.skip(reason='nyi')
def test_iot():
    pass

def test_cla():
    inst = asm.cla()
    bits = encode(inst)
    assert bits == 0x17
    pdp8 = PDP8([inst])
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_acc() == 0

def test_sna():
    inst = asm.sna()
    bits = encode(inst)
    assert bits == 0x14f
    pdp8 = PDP8([inst])
    pdp8.poke_acc(1)
    pdp8()
    assert pdp8.peak_pc() == 2
