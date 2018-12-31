import peak.pico.isa as isa
import peak.pico.asm as asm
from peak.bitfield import encode
import pytest

def test_reg():
    rega = isa.RegA(2)
    assert encode(rega) == 512
    regb = isa.RegB(2)
    assert encode(regb) == 32

def test_imm():
    imm = isa.Imm(2)
    assert encode(imm) == 2

def test_jmp():
    inst = asm.jmp(0)
    assert encode(inst) == 0xcf00

