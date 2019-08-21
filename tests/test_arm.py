import examples.arm.isa as isa
import examples.arm.asm as asm
from peak.bitfield import encode

def test_imm():
    imm = isa.Imm(3)
    assert encode(imm) == 3

def test_imm_operand():
    imm = isa.ImmOperand(isa.Imm(1),isa.Rotate(1))
    #assert encode(imm) == 0x101

def test_and():
    #and_ = isa.Inst(isa.BaseInst(isa.Data(isa.AND().reg(isa.R1,isa.R2,isa.R3))))
    and_ = asm.mov(asm.R0, asm.R1, imm=1)
    print( f'and {encode(and_):08x}' )
    #assert encode(and_) == 0xe0021000

def test_eor():
    #eor = isa.Inst(isa.BaseInst(isa.Data(isa.EOR().reg(isa.R1,isa.R2,isa.R3))))
    eor = asm.eor(asm.R0, asm.R1, imm=1)
    print( f'eor {encode(eor):08x}' )
    #assert encode(eor) == 0xe0221000

def test_mov():
    #mov = isa.Inst(isa.BaseInst(isa.Data(isa.MOV().reg(isa.R1,isa.R2,isa.R3))))
    #mov = asm.mov(asm.R1, asm.R2, asm.R3)
    #assert encode(mov) == 0xe0021000
    mov = asm.mov(asm.R0, asm.R1, imm=1)
    print( f'mov {encode(mov):08x}' )

def test_add():
    add = asm.add(asm.R1, asm.R0, imm=1)
    print( f'add {encode(add):08x}' )


def test_b():
    b = asm.b(0)
    print( f'b   {encode(b):08x}' )
    #assert encode(b) == 0xe0221000

def test_ldr():
    ldr = asm.ldr(asm.R0, asm.R1)
    print( f'ldr {encode(ldr):08x}' )
    #assert encode(br) == 0xe0221000

def test_str():
    str = asm.str(asm.R0, asm.R1)
    print( f'str {encode(str):08x}' )
    #assert encode(br) == 0xe0221000

#test_add()
#test_mov()
#test_b()
#test_ldr()
#test_str()



