import typing as tp

import coreir
from SMT_bit_vector import SMTBitVector, SMTSIntVector, SMTUIntVector
import smt_switch as ss

import itertools

__COREIR_TO_DUNDER = {
    'add' : '__add__',
    'sub' : '__sub__',
    'mul' : '__mul__',
    'shr' : '__rshit__',
    'shl' : '__lshift__',
    'or'  : '__or__',
    'and' : '__and__',
    'xor' : '__xor__',
    'not' : '__invert__',
}



def gen_mapping(solver : ss.smt,
        peak_component,
        instructions,
        static_inputs,
        free_inputs, #going to assume they are all of same type
        coreir_modules):
    mappings = {}
    args_labeled = list(free_inputs.items())
    args = [a[1] for a in args_labeled]
    arg0 = args[0]


    for mod in coreir_modules:
        if mod.name not in __COREIR_TO_DUNDER:
            mappings[mod] = None
            continue
        inputs = [k for k,v in mod.type.items() if v.is_input()]
        f  = getattr(type(arg0), __COREIR_TO_DUNDER[mod.name])

        found=False
        #try each permutation of inputs
        for perm in itertools.permutations(args, len(inputs)):
            try:
                core_smt = f(*perm)
            except TypeError as e:
                mappings[mod] = None
                continue
            arg_map = { i : a for i,a in zip(inputs, perm)}

            for inst in instructions:
                rvals = peak_component(inst, **static_inputs, **free_inputs)
                for idx, bv in enumerate(rvals):
                    if isinstance(bv, SMTBitVector) and bv.value.sort == core_smt.value.sort:
                        solver.Push()
                        solver.Assert(bv.value != core_smt.value)
                        if not solver.CheckSat():
                            ports_to_peak = {k1 : k2 for k1, v1 in arg_map.items() for k2, v2 in free_inputs.items() if v1 is v2}
                            mappings[mod] = {
                                    'instruction' : inst,
                                    'rval idx' : idx,
                                    'smt formula' : core_smt,
                                    'ports to smt' : arg_map,
                                    'ports to peak' : ports_to_peak,
                                    }
                            found=True
                            solver.Pop()
                        else:
                            solver.Pop()

                    if found:
                        break
                if found:
                    break
            if found:
                break
        else:
            mappings[mod] = None

    return mappings
