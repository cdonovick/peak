from .isa import *
from peak import Peak, gen_register, RAM

ZERO = Bit(0)
ONE = Bit(1)

class PDP8(Peak):

    def __init__(self, mem):
        family = Bit.get_family()

        self.pc = gen_register(family, Word, Word(0))()
        # 32 pages of 128 words
        self.mem = RAM(Word, 4096, mem, Word(0)) #
        self.acc = gen_register(family, Word, Word(0))()
        self.lnk = gen_register(family, Bit, ZERO)()

    def __call__(self):
        # phase 0
        pc = self.pc(0,0)
        inst = self.load(pc)
        pc = pc + 1

        type, inst = inst.match()

        if isinstance(inst, MRI):
            addr = inst.addr
            if inst.p == ZERO:
                page = BitVector[5](0)
            else:
                page = (pc-1)[7:]
            addr = Word(addr) # concat

            # phase 1
            if inst.i == IA.INDIRECT:
                addr = self.load(addr)

            # phase 2
            if   type == AND:
                data = self.load(addr)
                self.acc(self.acc(0,0) & data, 1)
            elif type == TAD:
                # add link
                data = self.load(addr)
                self.acc(self.acc(0,0) + data, 1)
            elif type == ISZ:
                data = self.load(addr) + 1
                self.store(addr, data)
                if data == 0:
                    pc = pc + 1
            elif type == DCA:
                self.store(addr, self.acc(0,0))
                self.acc(0,1)
            elif type == JMP:
                pc = addr
            elif type == JMS:
                self.store(addr,pc)
                pc = addr + 1

        elif type == OPR:
            type, inst = inst.match()
            if type == OPR1:
                if inst.cla:
                    self.acc(0,1)
                if inst.cma:
                    self.acc(~self.acc(0,0),1)
                if inst.iac:
                    self.acc(self.acc(0,0)+1,1)
                if inst.ral:
                    pass
                if inst.rar:
                    pass
            elif type == OPR2:
                skip = ZERO
                if   inst.sma == ONE:
                    if inst.skip == ZERO:
                        skip |= self.acc(0,0)[-1] == ONE
                    else:
                        skip |= self.acc(0,0)[-1] == ZERO
                elif inst.sza == ONE:
                    if inst.skip == ZERO:
                        skip |= self.acc(0,0) == Word(0)
                    else:
                        skip |= self.acc(0,0) != Word(0)
                elif inst.snl == ONE:
                    pass
                else:
                    skip = inst.skip == ONE
                if skip == ONE:
                    pc = pc + 1

        self.pc(pc, 1)

    def load(self, addr):
        return self.mem(addr, 0, 0)

    def store(self, addr, data):
        return self.mem(addr, data, 1)


    # testing interface to state

    def peak_pc(self):
        return int(self.pc(0,0))

    def poke_pc(self, value):
        return int(self.pc(Word(value), 1))

    def peak_acc(self):
        return int(self.acc(0, 0))

    def poke_acc(self, value):
        return int(self.acc(Word(value),1))

    def peak_lnk(self):
        return int(self.lnk(0,0))

    def poke_lnk(self, value):
        return int(self.lnk(Word(value),1))

    def peak_mem(self, addr):
        return int(self.mem(Word(addr),0,0))

    def poke_mem(self, addr, value):
        return int(self.mem(Word(addr),Word(value),wen=1))
