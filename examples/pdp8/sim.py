from .isa import *
from peak import Peak, gen_register, gen_RAM

ZERO = Bit(0)
ONE = Bit(1)

MAX_MEMORY = 4096

class PDP8(Peak):

    def __init__(self, mem):
        # 32 pages of 128 words
        self.mem = gen_RAM(Inst, depth=MAX_MEMORY)(mem, default_init=Word(0))
        self.pc = gen_register(Word)(Word(0))
        self.acc = gen_register(Word)(Word(0))
        self.lnk = gen_register(Bit)(ZERO)
        self.running = gen_register(Bit)(ONE)

    def __call__(self):
        if not self.is_running():
            return
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
            addr = Word(addr).concat(page) 

            # phase 1
            if inst.i == IA.INDIRECT:
                addr = self.load(addr)

            # phase 2
            if   type == AND:
                data = self.load(addr)
                self.acc(self.acc(0,0) & data, 1)
            elif type == TAD:
                data = self.load(addr).concat(BitVector[1](0))
                acc = self.acc(0,0).concat(BitVector[1](self.lnk(0,0)))
                res = acc + data
                self.acc(res[0:WIDTH], 1)
                self.lnk(res[WIDTH], 1)
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
                # Note that the order of these operations is specified
                if inst.cla: # clear accumulator
                    self.acc(Word(0),1)
                if inst.cma: # complement accumulator
                    self.acc(~self.acc(0,0),1)
                if inst.cll: # clear link
                    self.lnk(ZERO,1)
                if inst.cml: # complement link
                    self.lnk(~self.lnk(0,0),1)
                if inst.iac: # increment accumulator
                    self.acc(self.acc(0,0)+1,1)
                if inst.ral: # rotate left
                    acc = self.acc(0,0).concat(BitVector[1](self.lnk(0,0)))
                    res = acc.bvrol(2 if inst.twice else 1)
                    self.acc(res[0:WIDTH], 1)
                    self.lnk(res[WIDTH], 1)
                if inst.rar: # rotate right
                    acc = self.acc(0,0).concat(BitVector[1](self.lnk(0,0)))
                    res = acc.bvror(2 if inst.twice else 1)
                    print('rar', res)
                    self.acc(res[0:WIDTH], 1)
                    self.lnk(res[WIDTH], 1)
            elif type == OPR2:
                # Note that the order of these operations is specified
                if inst.sma == ONE \
                or inst.sza == ONE \
                or inst.snl == ONE \
                or inst.skip == ONE:
                    if inst.skip == ZERO:
                        skip = ZERO
                        if inst.sma == ONE: 
                            skip |= self.acc(0,0)[-1] == ONE
                        if inst.sza == ONE:
                            skip |= self.acc(0,0) == Word(0)
                        if inst.snl == ONE:
                            skip |= self.lnk(0,0) == ZERO
                    else:
                        skip = ONE
                        if inst.sma == ONE \
                        or inst.sza == ONE \
                        or inst.snl == ONE:
                            if inst.sma == ONE: # smp
                                skip &= self.acc(0,0)[-1] == ZERO
                            if inst.sza == ONE: # sna
                                skip &= self.acc(0,0) != Word(0)
                            if inst.snl == ONE: # szl
                                skip &= self.lnk(0,0) == ONE
                    if skip == ONE:
                        pc = pc + 1
                if inst.cla:
                    self.acc(Word(0),1)
                if inst.hlt:
                    self.running(ZERO, 1)

        self.pc(pc, 1)

    def is_running(self):
        return self.running(0,0) == ONE

    def run(self):
        while self.is_running():
            self()

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
        return int(self.lnk(Bit(value),1))

    def peak_mem(self, addr):
        return int(self.mem(Word(addr),0,0))

    def poke_mem(self, addr, value):
        return int(self.mem(Word(addr),Word(value),wen=1))
