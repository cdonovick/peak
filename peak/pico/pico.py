from bit_vector import BitVector
from .isa import *
from .. import Peak, Register, RAM, ROM

LR = Reg4(15)
ZERO = Bit(0)
ONE = Bit(1)

def zext(x,n):
    return BitVector(x.bits()+n*[0])

def adc(a:Word,b:Word,c:Bit):
    #print('a',a.bits(),len(a))
    #print('b',b.bits())
    #print('c',c.bits())
    a = zext(a,1)
    b = zext(b,1)
    c = zext(c,16)
    #print('a',a.bits(),len(a))
    #print('b',b.bits())
    #print('c',c.bits())
    res = a + b + c
    #print('res',res.bits())
    return res[0:-1], Bit(res[-1])

class Arith(Peak):
    def __call__(self, inst:Inst, a:Word, b:Word, c:Bit):
        if   inst.op == Arith_Op.Add:
            return adc(a,b,ZERO)
        elif inst.op == Arith_Op.Sub:
            return adc(a,~b,ONE)
        elif inst.op == Arith_Op.Adc:
            return adc(a,b,c)
        elif inst.op == Arith_Op.Sbc:
            return adc(a,~b,~c)
        else:
            raise NotImplemented(inst.op)

class Logic(Peak):
    def __call__(self, inst:Inst, a:Word, b:Word):
        if   inst.op == Logic_Op.Mov:
            return b
        elif inst.op == Logic_Op.And:
            return a & b
        elif inst.op == Logic_Op.Or:
            return a | b
        elif inst.op == Logic_Op.XOr:
            return a ^ b
        else:
            raise NotImplemented(inst.op)

class ALU(Peak):
    def __init__(self):
        self.arith = Arith()
        self.logic = Logic()

    def __call__(self, alu, a:Word, b:Word, C:Bit):

        if type(alu) == LogicInst:
            res = self.logic(alu, a, b)
            Z = res == 0
            N = res[-1]
            C = None
            V = None
        elif  type(alu) == ArithInst:
            res, res_p = self.arith(alu, a, b, C)
            Z = res == 0
            N = res[-1]
            C = res_p
            V = (a[-1] & b[-1] & ~N) or (~a[-1] & ~b[-1] & N)
        else:
            raise NotImplementedError(alu)

        return res, Z, N, C, V

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

        self.alu = ALU()

    def __call__(self):
        pc = self.PC()
        inst = self.mem(pc)
        insttype = type(inst)
        if insttype in ALUInst:
            ra = self.reg(inst.ra)
            rb = self.reg(inst.rb)
            res, Z, N, C, V = self.alu(inst, ra, rb, self.C())
            self.reg(inst.ra,res)
            self.Z(Z)
            self.N(N)
            self.C(C, C is not None)
            self.V(V, V is not None)
            self.PC(self.PC()+1)
        elif insttype in MemInst:
            if   type(inst) == LDLO:
                self.reg(inst.ra,Word(inst.imm))
            elif type(inst) == LDHI:
                self.reg(inst.ra,Word(inst.imm << 8))
            elif type(inst) == ST:
                if inst.imm == 0:
                    print(f'st {self.reg(inst.ra)}')
            else:
                raise NotImplemented(inst)
            self.PC(self.PC()+1)
        elif insttype in ControlInst:
            if cond(inst.cond, self.Z(), self.N(), self.C(), self.V()):
                if     type(inst) == Jump:
                    self.PC(Word(inst.imm))
                elif   type(inst) == Call:
                    self.reg(LR, pc+1)
                    self.PC(Word(inst.imm))
                elif   type(inst) == Return:
                    self.PC(self.reg(LR))
                else:
                    raise NotImplemented(inst)
            else:
                self.PC(self.PC()+1)
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
