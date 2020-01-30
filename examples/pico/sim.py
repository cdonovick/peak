from hwtypes import BitVector, overflow
from .isa import *
from peak import Peak, gen_register2, RAM, ROM

LR = Reg4(15)
ZERO = Bit(0)
ONE = Bit(1)

def arith(inst, a:Word, b:Word, c:Bit) :
    if   inst == Add:
        return a.adc(b,ZERO)
    elif inst == Sub:
        return a.adc(~b,ONE)
    elif inst == Adc:
        return a.adc(b,c)
    elif inst == Sbc:
        return a.adc(~b,~c)
    else:
        raise NotImplemented(inst)

def logic(inst, a:Word, b:Word):
    if   inst == Mov:
        return b
    elif inst == And:
        return a & b
    elif inst == Or:
        return a | b
    elif inst == XOr:
        return a ^ b
    else:
        raise NotImplemented(inst)

def cond(code, Z, N, C, V):
    if   code == Cond.Z:
        return Z
    elif code == Cond.Z_n:
        return not Z
    elif code == Cond.C or code == Cond.UGE:
        return C
    elif code == Cond.C_n or code == Cond.ULT:
        return not C
    elif code == Cond.N:
        return N
    elif code == Cond.N_n:
        return not N
    elif code == Cond.V:
        return V
    elif code == Cond.V_n:
        return not V
    elif code == Cond.UGT:
        return C and not Z
    elif code == Cond.ULE:
        return not C or Z
    elif code == Cond.SGE:
        return N == V
    elif code == Cond.SLT:
        return N != V
    elif code == Cond.SGT:
        return not Z and (N == V)
    elif code == Cond.SLE:
        return Z or (N != V)
    elif code == Cond.Never:
        return Bit(0)
    elif code == Cond.Always:
        return Bit(1)

class Pico(Peak):

    def __init__(self, mem):
        family = Bit.get_family()
        self.mem = ROM(Inst, 256, mem, Word(0))

        self.reg = RAM(Word, 16, [Word(0) for i in range(16)])
        self.PC = gen_register2(family, Word, Word(0))()
        self.Z = gen_register2(family, Bit, ZERO)()
        self.N = gen_register2(family, Bit, ZERO)()
        self.C = gen_register2(family, Bit, ZERO)()
        self.V = gen_register2(family, Bit, ZERO)()

    def __call__(self) -> None:
        pc = self.PC(0, 0)
        inst = self.mem(pc)
#        type, inst = inst.match()
        type, inst = inst._value_.__class__, inst._value_
        if type == Logic or type == Arith:
            self.alu(type, inst)
        elif type == Memory:
            self.memory(inst)
        elif type == Control:
            self.control(inst)
        else:
            raise NotImplemented(inst)

    def alu(self, type, inst):
#        subtype, inst = inst.match()
        subtype, inst = inst._value_.__class__, inst._value_
        a = self.reg(inst.ra, 0, 0)
        b = self.reg(inst.rb, 0, 0)
        if type == Logic:
            res = logic(subtype, a, b)
        else:
            res, res_p = arith(subtype, a, b, self.C(0, 0))
        self.reg(inst.ra,res, 1)
        self.Z(res==0, 1)
        self.N(Bit(res[-1]), 1)
        if type == Arith:
            self.C(res_p, 1)
            self.V(overflow(a,b,res), 1)
        self.PC(self.PC(0, 0)+1, 1)

    def memory(self, inst):
#        type, inst = inst.match()
        type, inst = inst._value_.__class__, inst._value_
        if   type == LDLO:
            self.reg(inst.ra,Word(inst.imm), 1)
        elif type == LDHI:
            self.reg(inst.ra,Word(int(inst.imm) << 8), 1)
        elif type == ST:
            if inst.imm == 0:
                print(f'st {self.reg(inst.ra, 0, 0)}')
        else:
            raise NotImplemented(inst)
        self.PC(self.PC(0, 0)+1, 1)

    def control(self, inst):
#        type, inst = inst.match()
        type, inst = inst._value_.__class__, inst._value_
        if     type == Jump:
            if cond(inst.cond, self.Z(0, 0), self.N(0, 0), self.C(0, 0), self.V(0, 0)):
                self.PC(Word(inst.imm), 1)
            else:
                self.PC(self.PC(0, 0)+1, 1)
        elif   type == Call:
            if cond(inst.cond, self.Z(0, 0), self.N(0, 0), self.C(0, 0), self.V(0, 0)):
                self.reg(LR, self.PC(0, 0)+1, 1)
                self.PC(Word(inst.imm), 1)
            else:
                self.PC(self.PC(0, 0)+1, 1)
        elif   type == Return:
            if cond(inst.cond, self.Z(0, 0), self.N(0, 0), self.C(0, 0), self.V(0, 0)):
                self.PC(self.reg(LR, 0, 0), 1)
            else:
                self.PC(self.PC(0, 0)+1, 1)
        else:
            raise NotImplemented(inst)

    # testing interface

    def peak_flag(self, flag):
        if   flag == 'Z':
            return self.Z(0, 0)
        elif flag == 'N':
            return self.N(0, 0)
        elif flag == 'C':
            return self.C(0, 0)
        elif flag == 'V':
            return self.C(0, 0)
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
        return int(self.PC(0, 0))

    def poke_pc(self, value):
        return int(self.PC(Word(value)))

    def peak_reg(self, addr):
        return int(self.reg(Reg4(addr), 0, 0))

    def poke_reg(self, addr, value):
        return int(self.reg(Reg4(addr),Word(value),wen=1))

    def peak_mem(self, addr):
        return int(self.mem(Word(addr)))

    def poke_mem(self, addr, value):
        return int(self.mem(Word(addr),Word(value),wen=1))
