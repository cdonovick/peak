import examples.pico.isa as isa
import examples.pico.asm as asm
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

@pytest.mark.skip
def test_jmp():
    inst = asm.jmp(0)
    assert encode(inst) == 0xcf00

