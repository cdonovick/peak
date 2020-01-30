from .peak import Peak
from .register import gen_register2
from hwtypes import BitVector

class ROM(Peak, gen_input_t=False, gen_output_t=False):
    def __init__(self, type, n, mem, init=0):
        self.mem = []
        for i in range(n):
            data = mem[i] if i < len(mem) else init
            self.mem.append( gen_register2(BitVector.get_family(), type, init=data)() )

    def __call__(self, addr):
        return self.mem[int(addr)](0, 0)

class RAM(ROM, gen_input_t=False, gen_output_t=False):
    def __call__(self, addr, data, wen):
        return self.mem[int(addr)](data, wen)

Memory = RAM
