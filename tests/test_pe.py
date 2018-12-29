import peak.pe.isa as isa
from peak.pe.pe import gen_pe, Bit, Data

PE = gen_pe(isa.Inst, 2)

def test_add():
    pe = PE()
    inst = isa.Add()
    res, res_p, irq = pe(inst, [Data(1),Data(3)])
    assert res==4
    assert res_p==0
    assert irq==0

def test_sub():
    pe = PE()
    inst = isa.Sub()
    res, res_p, irq = pe(inst, [Data(1),Data(3)])
    assert res==-2
    assert res_p==0
    assert irq==0
