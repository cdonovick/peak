from examples.min_pe2.sim import PE_fc
import magma
from peak.assembler import Assembler
from peak import wrap_with_disassembler
from hwtypes import Bit



PE_magma = PE_fc(magma.get_family())

magma.compile(f"examples/build/PE", PE_magma, output="coreir-verilog")