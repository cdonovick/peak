from peak.alu import *
from hwtypes import BitVector

PE = gen_alu(BitVector.get_family())

def test_add():
    inst = Inst(ALUOP.Add)
    assert Data(9) == PE(inst,Data(4), Data(5))
    assert Data(1) == PE(inst,Data(0), Data(1))

if  __name__ == '__main__':
    test_add()

