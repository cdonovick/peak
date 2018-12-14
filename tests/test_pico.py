from peak.pico import Pico
from peak.pico.isa import jmp, mov, and_, or_, xor, ldlo, ldhi, LDLO

def test_jmp():
    mem = [jmp(0)]
    pico = Pico(mem)
    assert pico.peak_pc() == 0
    pico()
    assert pico.peak_pc() == 0

def test_ldlo():
    mem = [ldlo(0,10)]
    pico = Pico(mem)
    pico()
    assert pico.peak_pc() == 1
    assert pico.peak_reg(0) == 10

def test_or():
    mem = [ldlo(0,1),ldlo(1,2),or_(0,1)]
    pico = Pico(mem)
    pico()
    pico()
    pico()
    assert pico.peak_pc() == 3
    assert pico.peak_reg(0) == 3
