import examples.pe1.asm as asm
from examples.pe1 import PE, Bit, Data

def test_and():
    # instantiate an PE - calls PE.__init__
    pe = PE()
    # format an 'and' instruction
    inst = asm.and_()
    # execute PE instruction with the arguments as inputs -  call PE.__call__
    res, res_p, irq = pe(inst, Data(1), Data(3))
    assert res==1
    assert res_p==0
    assert irq==0

def test_or():
    pe = PE()
    inst = asm.or_()
    res, res_p, irq = pe(inst, Data(1),Data(3))
    assert res==3
    assert res_p==0
    assert irq==0

def test_xor():
    pe = PE()
    inst = asm.xor()
    res, res_p, irq = pe(inst, Data(1),Data(3))
    assert res==2
    assert res_p==0
    assert irq==0

def test_inv():
    pe = PE()
    inst = asm.sub()
    res, res_p, irq = pe(inst, Data(0xffff),Data(1))
    assert res==0xfffe
    assert res_p==0
    assert irq==0

def test_neg():
    pe = PE()
    inst = asm.neg()
    res, res_p, irq = pe(inst, Data(0),Data(1))
    assert res==0xffff
    assert res_p==0
    assert irq==0

def test_add():
    pe = PE()
    inst = asm.add()
    res, res_p, irq = pe(inst, Data(1),Data(3))
    assert res==4
    assert res_p==0
    assert irq==0

def test_sub():
    pe = PE()
    inst = asm.sub()
    res, res_p, irq = pe(inst, Data(1),Data(3))
    assert res==-2
    assert res_p==0
    assert irq==0

def test_mult0():
    pe = PE()

    inst = asm.umult0()
    res, res_p, irq = pe(inst, Data(2),Data(3))
    assert res==6
    assert res_p==0
    assert irq==0

    inst = asm.smult0()
    res, res_p, irq = pe(inst, Data(-2),Data(3))
    assert res==-6
    assert res_p==0
    assert irq==0

def test_mult1():
    pe = PE()

    inst = asm.umult1()
    res, res_p, irq = pe(inst, Data(0x200),Data(3))
    assert res==6
    assert res_p==0
    assert irq==0

    inst = asm.smult1()
    res, res_p, irq = pe(inst, Data(-512),Data(3))
    assert res==-6
    assert res_p==0
    assert irq==0

def test_mult2():
    pe = PE()

    inst = asm.umult2()
    res, res_p, irq = pe(inst, Data(0x200),Data(0x300))
    assert res==6
    assert res_p==0
    assert irq==0

    inst = asm.smult2()
    res, res_p, irq = pe(inst, Data(-2*256),Data(3*256))
    assert res==-6
    assert res_p==0
    assert irq==0


def test_lsl():
    pe = PE()
    inst = asm.lsl()
    res, res_p, irq = pe(inst, Data(2),Data(1))
    assert res==4
    assert res_p==0
    assert irq==0

def test_lsr():
    pe = PE()
    inst = asm.lsr()
    res, res_p, irq = pe(inst, Data(2),Data(1))
    assert res==1
    assert res_p==0
    assert irq==0

def test_asr():
    pe = PE()
    inst = asm.asr()
    res, res_p, irq = pe(inst, Data(-2),Data(1))
    assert res==65535
    assert res_p==0
    assert irq==0

def test_sel():
    pe = PE()
    inst = asm.sel()
    res, res_p, irq = pe(inst, Data(1),Data(2),Bit(0))
    assert res==2
    assert res_p==0
    assert irq==0

def test_umin():
    pe = PE()
    inst = asm.umin()
    res, res_p, irq = pe(inst, Data(1),Data(2))
    assert res==1
    assert res_p==0
    assert irq==0

def test_umax():
    pe = PE()
    inst = asm.umax()
    res, res_p, irq = pe(inst, Data(1),Data(2))
    assert res==2
    assert res_p==0
    assert irq==0

def test_smin():
    pe = PE()
    inst = asm.smin()
    res, res_p, irq = pe(inst, Data(1),Data(2))
    assert res==1
    assert res_p==0
    assert irq==0

def test_smax():
    pe = PE()
    inst = asm.smax()
    res, res_p, irq = pe(inst, Data(1),Data(2))
    assert res==2
    assert res_p==0
    assert irq==0

def test_abs():
    pe = PE()
    inst = asm.abs()
    res, res_p, irq = pe(inst,Data(-1))
    assert res==1
    assert res_p==0
    assert irq==0

def test_eq():
    pe = PE()
    inst = asm.eq()
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==1

def test_ne():
    pe = PE()
    inst = asm.ne()
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==0

def test_uge():
    pe = PE()
    inst = asm.uge()
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==1

def test_ule():
    pe = PE()
    inst = asm.ule()
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==1

def test_ugt():
    pe = PE()
    inst = asm.ugt()
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==0

def test_ult():
    pe = PE()
    inst = asm.ult()
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==0

def test_sge():
    pe = PE()
    inst = asm.sge()
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==1

def test_sle():
    pe = PE()
    inst = asm.sle()
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==1

def test_sgt():
    pe = PE()
    inst = asm.sgt()
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==0

def test_slt():
    pe = PE()
    inst = asm.slt()
    res, res_p, irq = pe(inst,Data(1),Data(1))
    assert res_p==0

