from examples.pe import gen_pe, Bit, Data
import examples.pe.asm as asm

PE = gen_pe(2)

def test_and():
    pe = PE()
    inst = asm.and_()
    res, res_p, irq = pe(inst, [Data(1), Data(3)])
    assert res==1
    assert res_p==0
    assert irq==0

def test_or():
    pe = PE()
    inst = asm.or_()
    res, res_p, irq = pe(inst, [Data(1),Data(3)])
    assert res==3
    assert res_p==0
    assert irq==0

def test_xor():
    pe = PE()
    inst = asm.xor()
    res, res_p, irq = pe(inst, [Data(1),Data(3)])
    assert res==2
    assert res_p==0
    assert irq==0


def test_add():
    pe = PE()
    inst = asm.add()
    res, res_p, irq = pe(inst, [Data(1),Data(3)])
    assert res==4
    assert res_p==0
    assert irq==0

def test_sub():
    pe = PE()
    inst = asm.sub()
    res, res_p, irq = pe(inst, [Data(1),Data(3)])
    assert res==-2
    assert res_p==0
    assert irq==0

