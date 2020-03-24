from examples.demo_pes.pe7 import PE_fc
from examples.demo_pes.pe7.isa import Op
import magma
from peak.assembler import Assembler
from peak import wrap_with_disassembler
from hwtypes import Bit

class HashableDict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.keys())))

PE_bv = PE_fc(Bit.get_family())
PE_magma = PE_fc(magma.get_family())

inst_name = 'inst'
inst_type = PE_bv.input_t.field_dict[inst_name]

_assembler = Assembler(inst_type)
assembler = _assembler.assemble
disassembler = _assembler.disassemble
width = _assembler.width
layout = _assembler.layout
instr_magma_type = type(PE_magma.interface.ports[inst_name])
pe_circuit = wrap_with_disassembler(PE_magma, disassembler, width, HashableDict(layout), instr_magma_type)