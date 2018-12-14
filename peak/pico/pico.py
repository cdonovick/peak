from .isa import *
from .. import Peak, Register, RAM, ROM

class Arith(Peak):
    def __call__(self, inst:Inst, a:Word, b:Word, c:Bit):
        if   inst.op == Arith_Op.Add:
            return a + b
        elif inst.op == Arith_Op.Sub:
            return a - b
        elif inst.op == Arith_Op.Adc:
            return a + b + c
        elif inst.op == Arith_Op.Sbc:
            return a - b - c
        else:
            raise NotImplemented(inst.op)

class Logic(Peak):
    def __call__(self, inst:Inst, a:Word, b:Word):
        if   inst.op == Logic_Op.Mov:
            return a
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
            print(a,b,res)
            Z = res == 0
            N = res[-1]
            C = None
            V = None
        elif  type(alu) == ArithInst:
            res = self.arith(alu, a, b, C)
            res_p = 0
            Z = res == 0
            N = res[-1]
            C = res_p
            V = (a[-1] & b[-1] & ~N) or (~a[-1] & ~b[-1] & N)
        else:
            raise NotImplementedError(alu)

        return res, Z, N, C, V


class Pico(Peak):

    def __init__(self, mem):
        self.mem = ROM(Word, 256, mem, Word(0))

        self.reg = RAM(Word, 16, [Word(0) for i in range(16)])
        self.PC = Register(Word)
        self.Z = Register(Bit)
        self.N = Register(Bit)
        self.C = Register(Bit)
        self.V = Register(Bit)

        self.alu = ALU()

    def __call__(self):
        inst = self.mem(self.PC())
        insttype = type(inst)
        if insttype in ALUInst:
            ra = self.reg(inst.ra)
            rb = self.reg(inst.rb)
            res, Z, N, C, V = self.alu(inst, ra, rb, self.C())
            self.reg(inst.ra,res,wen=1)
            self.Z(Z)
            self.N(N)
            self.C(C, C is not None)
            self.V(V, V is not None)
            self.PC(self.PC()+1)
        elif insttype in MemInst:
            if   type(inst) == LDLO:
                self.reg(inst.ra,Word(inst.imm),wen=1)
            elif type(inst) == LDHI:
                self.reg(inst.ra,Word(inst.imm << 8),wen=1)
            else:
                raise NotImplemented(inst)
            self.PC(self.PC()+1)
        elif insttype in ControlInst:
            if   type(inst) == Jump:
                self.PC(Word(inst.imm))
            else:
                raise NotImplemented(inst)
        else:
            raise NotImplemented(inst)

    def peak_flag(self, flag):
        if   flag == 'Z':
            return int(self.Z())
        elif flag == 'N':
            return int(self.N())
        raise NotImplemented(flag)

    def poke_flag(self, flag, value):
        if   flag == 'Z':
            return int(self.Z(Bit(value)))
        elif flag == 'N':
            return int(self.N(Bit(value)))
        raise NotImplemented(flag)

    def peak_pc(self):
        return int(self.PC())

    def poke_pc(self, value):
        return int(self.PC(Word(value)))

    def peak_reg(self, addr):
        return int(self.reg(Reg4(addr)))

    def poke_reg(self, addr, value):
        return int(self.reg(Reg4(addr)),value,wen=1)

    def peak_mem(self, addr):
        return int(self.mem(Word(addr)))

    def poke_mem(self, addr, value):
        return int(self.mem(Word(addr),Word(value),wen=1))
