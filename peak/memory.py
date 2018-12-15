from .peak import Peak
from .register import Register

class ROM(Peak):
    def __init__(self, type, n, mem, init=0):
        self.mem = []
        for i in range(n):
            data = mem[i] if i < len(mem) else init
            self.mem.append( Register(type, data) )
        
    def __call__(self, addr):
        return self.mem[int(addr)]()

class RAM(ROM):
    def __call__(self, addr, data=None, wen=1):
        return self.mem[int(addr)](data, wen)

Memory = RAM
