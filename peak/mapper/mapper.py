import typing as tp
import itertools as it
import functools as ft
from ..peak import Peak
import coreir

from hwtypes import AbstractBitVector
from hwtypes import BitVector, SIntVector
from hwtypes import is_adt_type
from hwtypes.adt_meta import BoundMeta
from .SMT_bit_vector import SMTBit, SMTBitVector, SMTSIntVector

import pysmt.shortcuts as smt
from pysmt.logics import QF_BV

def _group_by_value(d : tp.Mapping[tp.Any, int]) -> tp.Mapping[int, tp.List[tp.Any]]:
    nd = {}
    for k,v in d.items():
        nd.setdefault(v, []).append(k)

    return nd

def _convert_io_types(peak_io):
    width_map = {}
    for name,btype in peak_io.items():
        if is_adt_type(btype):
            continue
        #Hack to get bitwidth of a hwtype
        width = 1 if not hasattr(btype,"size") else btype.size
        width_map[name] = width
    return width_map

def gen_mapping(
        peak_class : Peak,
        bv_isa : BoundMeta, #This is currently a hack that will be removed.
        smt_isa : BoundMeta,
        coreir_module : coreir.ModuleDef,
        coreir_model : tp.Callable,
        max_mappings : int,
        *,
        verbose : bool = False,
        solver_name : str = 'z3',
        constraints = []
        ):

    peak_inst = peak_class() #This cannot take any args

    peak_inputs = _convert_io_types(peak_class.__call__._peak_inputs_)
    peak_outputs = _convert_io_types(peak_class.__call__._peak_outputs_)

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
    def f_fun(inst):
        return all(constraint(inst) for constraint in constraints)
    bv_isa_list = list(filter(f_fun, bv_isa.enumerate()))
    bv_isa_len = len(bv_isa_list)
    smt_isa_list = list(filter(f_fun, smt_isa.enumerate()))
    smt_isa_len = len(smt_isa_list)

    for ii,smt_inst in enumerate(smt_isa_list):
        if verbose:
            print(f"inst {ii+1}/{isa_len}")
            print(smt_inst)

        for bi,binding in enumerate(bindings):
            binding_dict = {k : core_smt_vars[v] if v is not None else SMTBitVector[peak_inputs[k]](0) for v,k in binding}
            name_binding = {k : v if v is not None else 0 for v,k in binding}
            if verbose:
                print(f"binding {bi+1}/{len(bindings)}")

            rvals = peak_inst(smt_inst, **binding_dict)
            if not isinstance(rvals, tuple):
                rvals = rvals,

            for idx, bv in enumerate(rvals):
                if isinstance(bv, (SMTBit, SMTBitVector)) and bv.value.get_type() == core_smt_expr.value.get_type():
                    with smt.Solver(solver_name, logic=QF_BV) as solver:
                        expr = bv != core_smt_expr
                        solver.add_assertion(expr.value)
                        if not solver.solve():
                            #Create output and input map
                            output_map = {"out":list(peak_class.__call__._peak_outputs_.items())[idx][0]}
                            input_map = {}
                            for k,v in name_binding.items():
                                if v == 0:
                                    v = "0"
                                elif v == "in_":
                                    v = "in"
                                input_map[v] = k

                            mapping = dict(
                                instruction=bv_isa_list[ii],
                                output_map=output_map,
                                input_map=input_map
                            )
                            yield mapping
                            found  += 1
                            if found >= max_mappings:
                                return
