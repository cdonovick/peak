import typing as tp
import itertools as it
import functools as ft

import coreir

from hwtypes import AbstractBitVector
from ..adt import ISABuilder
from hwtypes import BitVector, SIntVector
from .SMT_bit_vector import SMTBit, SMTBitVector, SMTSIntVector

import pysmt.shortcuts as smt
from pysmt.logics import QF_BV


def _group_by_value(d : tp.Mapping[tp.Any, int]) -> tp.Mapping[int, tp.List[tp.Any]]:
    nd = {}
    for k,v in d.items():
        nd.setdefault(v, []).append(k)

    return nd


def gen_mapping(
        peak_component_generator : tp.Callable[[tp.Type[AbstractBitVector]], tp.Callable],
        isa : tp.Type[ISABuilder],
        coreir_module : coreir.ModuleDef,
        coreir_model : tp.Callable,
        max_mappings : int,
        *,
        solver_name : str = 'z3',
        ):

    smt_alu = peak_component_generator(SMTBitVector.get_family())
    #smt_alu, peak_inputs, peak_outputs = peak_component_generator(SMTBitVector.get_family())
    if isinstance(smt_alu,tuple):
        smt_alu, peak_inputs, peak_outputs = smt_alu
    else:
        if not hasattr(smt_alu, "_peak_inputs_"):
            raise ValueError("Need to wrap __call__ with @name_outputs")
        
        #Filter out the instruction
        peak_inputs = {}
        for k,v in smt_alu._peak_inputs_.items():
            if not issubclass(v,ISABuilder):
                peak_inputs[k] = v.size
        peak_outputs = {k:v.size for (k,v) in smt_alu._peak_outputs_.items() }

    core_inputs = {k if k != 'in' else 'in_' : v.size for k,v in coreir_module.type.items() if v.is_input()}
    core_outputs = {k : v.size for k,v in  coreir_module.type.items() if v.is_output()}
    core_smt_vars = {k : SMTBitVector[v]() for k,v in core_inputs.items()}
    core_smt_expr = coreir_model(**core_smt_vars)

    #The following is some really gross magic to generate all possible assignments
    #of core inputs / costants (None) to peak inputs
    core_inputs_by_size = _group_by_value(core_inputs)
    peak_inputs_by_size = _group_by_value(peak_inputs)

    assert core_inputs_by_size.keys() <= peak_inputs_by_size.keys()
    for k in core_inputs_by_size:
        assert len(core_inputs_by_size[k]) <= len(peak_inputs_by_size[k])

    possible_matching = {}
    for size, pi in peak_inputs_by_size.items():
        ci = core_inputs_by_size.setdefault(size, [])
        ci = list(it.chain(ci, it.repeat(None, len(pi) - len(ci))))
        assert len(ci) == len(pi)
        for perm in it.permutations(pi):
            possible_matching.setdefault(size, []).append(list(zip(ci, perm)))

    del core_inputs_by_size
    del peak_inputs_by_size

    bindings = []
    for l in it.product(*possible_matching.values()):
        bindings.append(list(it.chain(*l)))

    found = 0
    if found >= max_mappings:
        return
    for binding in bindings:
        binding_dict = {k : core_smt_vars[v] if v is not None else SMTBitVector[peak_inputs[k]](0) for v,k in binding}
        name_binding = {k : v if v is not None else 0 for v,k in binding}
        for inst in isa.enumerate():
            rvals = smt_alu(inst, **binding_dict)
            for idx, bv in enumerate(rvals):

                if isinstance(bv, (SMTBit,SMTBitVector)) and bv.value.get_type() == core_smt_expr.value.get_type():
                    with smt.Solver(solver_name, logic=QF_BV) as solver:
                        expr = bv != core_smt_expr
                        solver.add_assertion(expr.value)
                        if not solver.solve():
                            mapping = {
                                    'instruction' : inst,
                                    'output' : 'FLAG' if idx else 'RESULT',
    #                                'core to smt' : core_smt_vars,
    #                                'core smt formula' : core_smt_expr.value,
    #                                'peak smt formula' : bv.value,
                                    'coreir to peak' : {v if v != 0  else 'Constant 0' : k for k,v in name_binding.items()},
                            }
                            yield mapping
                            found  += 1
                            if found >= max_mappings:
                                return
