from bit_vector import BitVector
from .isa import *
from .. import Peak, Register, RAM, ROM

LR = Reg4(15)
ZERO = Bit(0)
ONE = Bit(1)

def zext(x,n):
    return BitVector(x.bits()+n*[0])

def adc(a:Word,b:Word,c:Bit):
    a = zext(a,1)
    b = zext(b,1)
    c = zext(c,16)
    res = a + b + c
    return res[0:-1], Bit(res[-1])

def arith(op:Arith_Op, a:Word, b:Word, c:Bit) :
    if   op == Arith_Op.Add:
        return adc(a,b,ZERO)
    elif op == Arith_Op.Sub:
        return adc(a,~b,ONE)
    elif op == Arith_Op.Adc:
        return adc(a,b,c)
    elif op == Arith_Op.Sbc:
        return adc(a,~b,~c)
    else:
        raise NotImplemented(inst.op)

def logic(op:Logic_Op, a:Word, b:Word):
        if   op == Logic_Op.Mov:
            return b
        elif op == Logic_Op.And:
            return a & b
        elif op == Logic_Op.Or:
            return a | b
        elif op == Logic_Op.XOr:
            return a ^ b
        else:
            raise NotImplemented(inst.op)

def cond(code, Z, N, C, V):
    if   code == Cond_Op.Z:
        return Z
    elif code == Cond_Op.Z_n:
        return not Z
    elif code == Cond_Op.C or code == Cond_Op.UGE:
        return C
    elif code == Cond_Op.C_n or code == Cond_Op.ULT:
        return not C
    elif code == Cond_Op.N:
        return N
    elif code == Cond_Op.N_n:
        return not N
    elif code == Cond_Op.V:
        return V
    elif code == Cond_Op.V_n:
        return not V
    elif code == Cond_Op.UGT:
        return C and not Z
    elif code == Cond_Op.ULE:
        return not C or Z
    elif code == Cond_Op.SGE:
        return N == V
    elif code == Cond_Op.SLT:
        return N != V
    elif code == Cond_Op.SGT:
        return not Z and (N == V)
    elif code == Cond_Op.SLE:
        return Z or (N != V)
    elif code == Cond_Op.Never:
        return Bit(0)
    elif code == Cond_Op.Always:
        return Bit(1)

class Pico(Peak):

    def __init__(self, mem):
        self.mem = ROM(Word, 256, mem, Word(0))

        self.reg = RAM(Word, 16, [Word(0) for i in range(16)])
        self.PC = Register(Word, Word(0))
        self.Z = Register(Bit,ZERO)
        self.N = Register(Bit,ZERO)
        self.C = Register(Bit,ZERO)
        self.V = Register(Bit,ZERO)

    def __call__(self):
        pc = self.PC()
        inst = self.mem(pc)
        type, inst = inst.match()
        if type == LogicInst or type == ArithInst:
            a = self.reg(inst.ra)
            b = self.reg(inst.rb)
            if type == LogicInst:
                res = logic(inst.op, a, b)
            else:
                res, res_p = arith(inst.op, a, b, self.C())
            self.reg(inst.ra,res)
            self.Z(res==0)
            N = self.N(Bit(res[-1]))
            if type == ArithInst:
                self.C(res_p)
                msba = Bit(a[-1])
                msbb = Bit(b[-1])
                self.V( (msba & msbb & ~N) or (~msba & ~msbb & N) )
            self.PC(self.PC()+1)
        elif type == MemInst:
            type, inst = inst.match()
            if   type == LDLO:
                self.reg(inst.ra,Word(inst.imm))
            elif type == LDHI:
                self.reg(inst.ra,Word(inst.imm << 8))
            elif type == ST:
                if inst.imm == 0:
                    print(f'st {self.reg(inst.ra)}')
            else:
                raise NotImplemented(inst)
            self.PC(self.PC()+1)
        elif type == ControlInst:
            type, inst = inst.match()
            if     type == Jump:
                if cond(inst.cond, self.Z(), self.N(), self.C(), self.V()):
                    self.PC(Word(inst.imm))
                else:
                    self.PC(self.PC()+1)
            elif   type == Call:
                if cond(inst.cond, self.Z(), self.N(), self.C(), self.V()):
                    self.reg(LR, pc+1)
                    self.PC(Word(inst.imm))
                else:
                    self.PC(self.PC()+1)
            elif   type == Return:
                if cond(inst.cond, self.Z(), self.N(), self.C(), self.V()):
                    self.PC(self.reg(LR))
                else:
                    self.PC(self.PC()+1)
            else:
                raise NotImplemented(inst)
        else:
            raise NotImplemented(inst)

    def peak_flag(self, flag):
        if   flag == 'Z':
            return int(self.Z())
        elif flag == 'N':
            return int(self.N())
        elif flag == 'C':
            return int(self.C())
        elif flag == 'V':
            return int(self.C())
        raise NotImplemented(flag)

    def poke_flag(self, flag, value):
        if   flag == 'Z':
            return int(self.Z(Bit(value)))
        elif flag == 'N':
            return int(self.N(Bit(value)))
        elif flag == 'C':
            return int(self.C(Bit(value)))
        elif flag == 'V':
            return int(self.V(Bit(value)))
        raise NotImplemented(flag)

    def peak_pc(self):
        return int(self.PC())

    def poke_pc(self, value):
        return int(self.PC(Word(value)))

    def peak_reg(self, addr):
        return int(self.reg(Reg4(addr)))

    def poke_reg(self, addr, value):
        return int(self.reg(Reg4(addr),Word(value),wen=1))

    def peak_mem(self, addr):
        return int(self.mem(Word(addr)))

    def poke_mem(self, addr, value):
        return int(self.mem(Word(addr),Word(value),wen=1))
