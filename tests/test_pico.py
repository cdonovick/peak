import random
from collections import namedtuple
from peak.pico import Pico, Word
import peak.pico.isa as isa
import pytest

def test_jmp():
    mem = [isa.jmp(0)]
    pico = Pico(mem)
    assert pico.peak_pc() == 0
    pico()
    assert pico.peak_pc() == 0

def test_ldlo():
    mem = [isa.ldlo(0,10)]
    pico = Pico(mem)
    pico()
    assert pico.peak_pc() == 1
    assert pico.peak_reg(0) == 10

def test_ldhi():
    mem = [isa.ldhi(0,10)]
    pico = Pico(mem)
    pico()
    assert pico.peak_pc() == 1
    assert pico.peak_reg(0) == 10 << 8

def test_lohi():
    mem = [isa.ldlo(0,1),isa.ldhi(1,2),isa.or_(0,1)]
    pico = Pico(mem)
    pico()
    pico()
    pico()
    assert pico.peak_pc() == 3
    assert pico.peak_reg(0) == (2<<8)|1


def alu(mem, op, ra, rb):
    pico = Pico(mem)
    pico.poke_reg(0,ra)
    pico.poke_reg(1,rb)
    pico()
    assert pico.peak_pc() == 1
    assert pico.peak_reg(0) == int(op(Word(ra),Word(rb)))

inst = namedtuple("inst", ["name", "func"])

NVALUES = 8
def random16():
    return random.randint(0,1<<16-1)
testvectors = [(random16(), random16()) for i in range(NVALUES)]

@pytest.mark.parametrize("op", [
    inst('mov',  lambda x, y: y),
    inst('and_', lambda x, y: x&y),
    inst('or_',  lambda x, y: x|y),
    inst('xor',  lambda x, y: x^y),
    inst('add',  lambda x, y: x+y),
    inst('adc',  lambda x, y: x+y),
    inst('sub',  lambda x, y: x-y),
    inst('sbc',  lambda x, y: x-y),
])
@pytest.mark.parametrize("ab", testvectors)
def test_alu(op,ab):
    alu( [getattr(isa,op.name)(0,1)], op.func, ab[0], ab[1] )

def test_cond():
    pico = Pico([isa.mov(0,1)])
    pico.poke_reg(1,-1)
    pico()
    assert pico.peak_flag('Z') == 0
    assert pico.peak_flag('N') == 1

def test_st():
    pico = Pico([isa.st(0,0)])
    pico.poke_reg(0,0xf)
    pico()

def test_call():
    pico = Pico([isa.call(2),isa.mov(0,0),isa.ret()])
    pico()
    assert pico.peak_pc() == 2
    assert pico.peak_reg(15) == 1
    pico()
    assert pico.peak_pc() == 1
    pico()
    assert pico.peak_pc() == 2


