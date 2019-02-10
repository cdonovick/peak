import functools as ft
from peak.demo_pe import sim
from peak.demo_pe import isa
from peak.mapper import SMTBitVector, ss
from peak.mapper import gen_mapping
import coreir

__COREIR_MODELS = {
        'add' : lambda in0, in1: in0.bvadd(in1),
        'sub' : lambda in0, in1: in0.bvsub(in1),
        'mul' : lambda in0, in1: in0.bvmul(in1),
        'shr' : lambda in0, in1: in0.bvashr(in1),
        'shl' : lambda in0, in1: in0.bvshl(in1),
        'or'  : lambda in0, in1: in0.bvor(in1),
        'and' : lambda in0, in1: in0.bvand(in1),
        'xor' : lambda in0, in1: in0.bvxor(in1),
        'not' : lambda in_: in_.bvnot(),
}

solver = ss.smt('Z3')
context = coreir.Context()
lib = context.get_namespace('coreir')
mods = []
for gen in lib.generators.values():
    if gen.params.keys() == {'width'}:
        mods.append(gen(width=sim.DATAWIDTH))

for mod in mods:
    if mod.name in __COREIR_MODELS:
        found = False
        for mapping in gen_mapping(
                solver,
                sim.gen_alu,
                isa.INST,
                mod,
                __COREIR_MODELS[mod.name],
                1,):
            print(f'Mapping found for {mod.name}')
            print(mapping)
            print()
            found = True
        if not found:
            print(f'No Mapping found for {mod.name}\n')
        solver.Reset()

