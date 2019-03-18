from peak.alu import ALU, Inst, ALUOP
from hwtypes import BitVector

alu = ALU(BitVector.get_family(),width=16)
Data = alu.Data

def test_add():
    inst = Inst(ALUOP.Add)
    assert Data(9) == alu(inst,Data(4), Data(5))
    assert Data(1) == alu(inst,Data(0), Data(1))

if  __name__ == '__main__':
    test_add()

