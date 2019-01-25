import functools as ft
from peak.pe1 import sim
from peak.pe1 import isa
from SMT_bit_vector import SMTBitVector, SMTSIntVector, SMTUIntVector, ss
from mapper import gen_mapping
import coreir


solver = ss.smt('Z3')

bound_BV = ft.partial(SMTBitVector, solver)
bound_SInt = ft.partial(SMTSIntVector, solver)
bound_UInt = ft.partial(SMTUIntVector, solver)

alu = sim.gen_alu(bound_BV, bound_SInt, bound_UInt)

static_inputs = {
    'signed' : 0,
    'd' : 0,
}

free_inputs = {
    'b' : bound_BV(None, sim.DATAWIDTH, name='x'),
    'a' : bound_BV(None, sim.DATAWIDTH, name='y'),
}


instructions = isa.ALU

context = coreir.Context()
lib = context.get_namespace('coreir')
mods = []
for gen in lib.generators.values():
    if gen.params.keys() == {'width'}:
        mods.append(gen(width=sim.DATAWIDTH))

mappings = gen_mapping(solver, alu, instructions, static_inputs, free_inputs, mods)

for k,v in mappings.items():
    if v is not None:
        print(f'Mapping found for coreir module named {k.name}')
        for k,v in v.items():
            print(f'\t{k} : {v}')
        print()
