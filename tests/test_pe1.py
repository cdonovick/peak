import peak.pe.isa1 as isa
from peak.pe.pe1 import PE, Bit, Data

def test_and():
    pe = PE()
    inst = isa.and_()
    res, res_p, irq = pe(inst, Data(1), Data(3))
    assert res==1
    assert res_p==0
    assert irq==0

def test_or():
    pe = PE()
    inst = isa.or_()
    res, res_p, irq = pe(inst, Data(1),Data(3))
    assert res==3
    assert res_p==0
    assert irq==0

def test_xor():
    pe = PE()
    inst = isa.xor()
    res, res_p, irq = pe(inst, Data(1),Data(3))
    assert res==2
    assert res_p==0
    assert irq==0

def test_inv():
    pe = PE()
    inst = isa.sub()
    res, res_p, irq = pe(inst, Data(-1),Data(1))
    assert res==0xfffe
    assert res_p==0
    assert irq==0

def test_neg():
    pe = PE()
    inst = isa.sub()
    res, res_p, irq = pe(inst, Data(0),Data(1))
    assert res==0xffff
    assert res_p==0
    assert irq==0

def test_add():
    pe = PE()
    inst = isa.add()
    res, res_p, irq = pe(inst, Data(1),Data(3))
    assert res==4
    assert res_p==0
    assert irq==0

def test_sub():
    pe = PE()
    inst = isa.sub()
    res, res_p, irq = pe(inst, Data(1),Data(3))
    assert res==-2
    assert res_p==0
    assert irq==0

def test_lsl():
    pe = PE()
    inst = isa.lsl()
    res, res_p, irq = pe(inst, Data(2),Data(1))
    assert res==4
    assert res_p==0
    assert irq==0

def test_lsr():
    pe = PE()
    inst = isa.lsr()
    res, res_p, irq = pe(inst, Data(2),Data(1))
    assert res==1
    assert res_p==0
    assert irq==0

def test_asr():
    pe = PE()
    inst = isa.asr()
    res, res_p, irq = pe(inst, Data(-2),Data(1))
    assert res==65535
    assert res_p==0
    assert irq==0

def test_sel():
    pe = PE()
    inst = isa.sel()
    res, res_p, irq = pe(inst, Data(1),Data(2),Bit(0))
    assert res==2
    assert res_p==0
    assert irq==0

def test_umin():
    pe = PE()
    inst = isa.umin()
    res, res_p, irq = pe(inst, Data(1),Data(2))
    assert res==1
    assert res_p==0
    assert irq==0

def test_umax():
    pe = PE()
    inst = isa.umax()
    res, res_p, irq = pe(inst, Data(1),Data(2))
    assert res==2
    assert res_p==0
    assert irq==0

def test_abs():
    pe = PE()
    inst = isa.abs()
    res, res_p, irq = pe(inst,Data(-1))
    assert res==1
    assert res_p==0
    assert irq==0

def test_eq():
    pe = PE()
    inst = isa.sub.flag(isa.Cond.EQ)
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==1

def test_ne():
    pe = PE()
    inst = isa.sub.flag(isa.Cond.NE)
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==0

def test_uge():
    pe = PE()
    inst = isa.sub.flag(isa.Cond.UGE)
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==1

def test_ule():
    pe = PE()
    inst = isa.sub.flag(isa.Cond.ULE)
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==1

def test_ugt():
    pe = PE()
    inst = isa.sub.flag(isa.Cond.UGT)
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==0

def test_ult():
    pe = PE()
    inst = isa.sub.flag(isa.Cond.ULT)
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==0



