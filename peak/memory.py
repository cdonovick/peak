from .peak import Peak
from .register import gen_register
from hwtypes import BitVector, Bit
import typing as tp

def gen_ROM(T, depth : int):
    class ROM(Peak):
        def __init__(self, init : tp.List[T], default_init : T):
            self.mem = []
            regT = gen_register(T)
            for i in range(depth):
                data = init[i] if i < len(init) else default_init
                self.mem.append( regT(data))

        def __call__(self, addr : int):
            return self.mem[int(addr)](0, Bit(0))
    return ROM

def gen_RAM(T, depth : int):
    ROM = gen_ROM(T,depth)
    class RAM(ROM):
        def __call__(self, addr : int, data : T, wen : Bit):
            return self.mem[int(addr)](data, wen)

    return RAM

gen_Memory = gen_RAM
