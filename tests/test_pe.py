from peak.pe import PE, Bit, Data
from peak.pe.isa import add, sub, and_, or_, xor

def test_and():
    pe = PE()
    inst = and_()
    res, res_p, irq = pe(inst, Data(1), Data(3))
    assert res==1
    assert res_p==0
    assert irq==0

def test_or():
    pe = PE()
    inst = or_()
    res, res_p, irq = pe(inst, Data(1),Data(3))
    assert res==3
    assert res_p==0
    assert irq==0

def test_xor():
    pe = PE()
    inst = xor()
    res, res_p, irq = pe(inst, Data(1),Data(3))
    assert res==2
    assert res_p==0
    assert irq==0

#def test_inv():
#    pe = PE()
#    inst = inv()
#    res, res_p, irq = pe(inst, Data(1),Data(3))
#    assert res==0xfffe
#    assert res_p==0
#    assert irq==0

def test_add():
    pe = PE()
    inst = add()
    res, res_p, irq = pe(inst, Data(1),Data(3))
    assert res==4
    assert res_p==0
    assert irq==0

def test_sub():
    pe = PE()
    inst = sub()
    res, res_p, irq = pe(inst, Data(1),Data(3))
    assert res==-2
    assert res_p==0
    assert irq==0


#def test_lshl():
#    a = pe.lshl()
#    res, res_p, irq = a(2,1)
#    assert res==4
#    assert res_p==0

#def test_shr():
#    a = pe.shr(False)
#    res, res_p, irq = a(2,1)
#    assert res==1
#    assert res_p==0

## def test_ashr():
##     a = pe.ashr()
##     res, res_p, irq = a(-2,1)
##     assert res==65535
##     assert res_p==0

#def test_sel():
#    a = pe.sel()
#    res, res_p, irq = a(1,2,0,0)
#    assert res==2

#def test_min():
#    a = pe.min(signed=0)
#    res, res_p, irq = a(1,2)
#    assert res==1
#    assert res_p==False

#def test_max():
#    a = pe.max(signed=0)
#    res, res_p, irq = a(1,2)
#    assert res==2
#    assert res_p==0

#def test_abs():
#    a = pe.abs()
#    res, res_p, irq = a(-1)
#    assert res==1

## TODO: eq implemented with sub + Z flag
## def test_eq():
##     a = pe.eq()
##     res, res_p, irq = a(1,2)
##     assert res_p==0

#def test_ge():
#    a = pe.ge(signed=0)
#    res, res_p, irq = a(1,2)
#    assert res_p==0

#def test_le():
#    a = pe.le(signed=0)
#    res, res_p, irq = a(1,2)
#    assert res_p==False


