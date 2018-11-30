from t import Bits, Enum, Struct, Union, match

Reg = Bits(4)

class Op(Enum):
    add = 0
    sub = 1

class Data(Struct):
    op : Op
    r0: Reg
    r1: Reg

Addr = Bits(5)

class Load(Struct):
    reg: Reg
    addr: Addr

Inst = Union[Data,Load]

r0 = Reg(0)
r1 = Reg(1)
inst0 = Load(r0,Addr(10))
inst1 = Load(r1,Addr(11))
inst2 = Data(Op.add, r0, r1)

def print_data(inst):
    print(inst.op.name, f'r{inst.r0}', f'r{inst.r1}')

def print_load(inst):
    print('ld', f'r{inst.reg}', inst.addr)

for inst in [inst0, inst1, inst2]:
    match(inst, {Data: print_data, Load: print_load})

