import random
from collections import namedtuple
from examples.pico import Pico, Word
import examples.pico.isa as isa
import examples.pico.asm as asm
import pytest

def test_ldlo():
    mem = [asm.ldlo(0,10)]
    pico = Pico(mem)
    pico()
    assert pico.peak_pc() == 1
    assert pico.peak_reg(0) == 10

def test_ldhi():
    mem = [asm.ldhi(0,10)]
    pico = Pico(mem)
    pico()
    assert pico.peak_pc() == 1
    assert pico.peak_reg(0) == 10 << 8

def test_ld():
    mem = [asm.ldlo(0,1), asm.ldhi(1,2), asm.or_(0,1)]
    pico = Pico(mem)
    pico()
    pico()
    pico()
    assert pico.peak_pc() == 3
    assert pico.peak_reg(0) == (2<<8)|1

def test_st():
    pico = Pico([asm.st(0,0)])
    pico.poke_reg(0,0xf)
    pico()

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
    alu( [getattr(asm,op.name)(0,1)], op.func, ab[0], ab[1] )

def test_cond():
    pico = Pico([asm.mov(0,1)])
    pico.poke_reg(1,-1)
    pico()
    assert pico.peak_flag('Z') == 0
    assert pico.peak_flag('N') == 1


def test_jump():
    mem = [asm.jmp(0)]
    pico = Pico(mem)
    assert pico.peak_pc() == 0
    pico()
    assert pico.peak_pc() == 0

def test_call():
    pico = Pico([asm.call(2),asm.mov(0,0),asm.ret()])
    pico()
    assert pico.peak_pc() == 2
    assert pico.peak_reg(15) == 1
    pico()
    assert pico.peak_pc() == 1
    pico()
    assert pico.peak_pc() == 2

#test_jump()
#test_call()

#test_ldlo()
#test_ldhi()
#test_ld()
#test_st()

#test_cond()
