import hwtypes
import functools as ft
from peak.mapper import SMTBitVector
from peak.mapper import gen_mapping
import coreir
import sys


if len(sys.argv) == 2:
    _demo_pe = __import__(f'peak.demo_pes.pe{sys.argv[1]}', fromlist=('sim', 'isa'))
else:
    print('Incorrect usage')
    print(f'{sys.argv[0]} <DEMO PE NUMBER>')
    sys.exit(1)
sim = _demo_pe.sim
isa = _demo_pe.isa
del _demo_pe


__COREIR_MODELS = {
        'add' : lambda in0, in1: in0.bvadd(in1),
        'sub' : lambda in0, in1: in0.bvsub(in1),
        'or'  : lambda in0, in1: in0.bvor(in1),
        'and' : lambda in0, in1: in0.bvand(in1),
        'shl' : lambda in0, in1: in0.bvshl(in1),
        'lshr': lambda in0, in1: in0.bvlshr(in1),
        'not' : lambda in_: in_.bvnot(),
        'neg' : lambda in_: in_.bvneg(),
        'eq'  : lambda in0, in1: in0.bveq(in1),
        'neq' : lambda in0, in1: in0.bvne(in1),
        'ult' : lambda in0, in1: in0.bvult(in1),
        'ule' : lambda in0, in1: in0.bvule(in1),
        'ugt' : lambda in0, in1: in0.bvugt(in1),
        'uge' : lambda in0, in1: in0.bvuge(in1),
        'xor' : lambda in0, in1: in0.bvxor(in1),
}

context = coreir.Context()
lib = context.get_namespace('coreir')
mods = []
for gen in lib.generators.values():
    if gen.params.keys() == {'width'}:
        mods.append(gen(width=sim.DATAWIDTH))

del lib
del context

for mod in mods:
    if mod.name in __COREIR_MODELS:
        found = False
        mappings = list(gen_mapping(
                sim.gen_alu(hwtypes.SMTBitVector.get_family()),
                isa.INST,
                isa.INST,
                mod,
                __COREIR_MODELS[mod.name],
                1,
#                verbose=True,
                ))
        if mappings:
            print(f'Mappings found for {mod.name}')
            for mapping in mappings:
                for k,v in mapping.items():
                    print(k, v)
        else:
            print(f'No Mapping found for {mod.name}')
        print('\n------------------------------------------------\n')

