from ..riscv.asm import *
from .isa import ISA_fc

isa = ISA_fc.Py


ASM_TEMPLATE = '''\
def asm_{inst_name}(rs=None, rd=None, rs1=None):
    if rd is None:
        raise ValueError('rd is required')

    if (rs is None) == (rs1 is None):
        raise ValueError('exactly one rs and rs1 is required')

    rs = isa.Idx(rs if rs1 is None else rs1)
    rd = isa.Idx(rd)

    data = isa.E(rd=rd, rs=rs)
    tag = isa.BitInst.{inst_name}

    return isa.Inst(isa.Ext(data, tag))
'''

for inst_name in isa.BitInst._field_table_:
    exec(ASM_TEMPLATE.format(inst_name=inst_name))
