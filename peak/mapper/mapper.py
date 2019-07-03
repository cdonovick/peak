import typing as tp
import itertools as it
import functools as ft
import logging
from ..peak import Peak, get_isa
import coreir
from .binding import Binder
from hwtypes import AbstractBitVector
from hwtypes import BitVector, SIntVector
from hwtypes import is_adt_type
from hwtypes.adt_meta import BoundMeta
from hwtypes import SMTBit, SMTBitVector, SMTSIntVector

import pysmt.shortcuts as smt
from pysmt.logics import QF_BV

def _filter_adt_types(peak_io):
    io_map = {}
    for name,btype in peak_io.items():
        if is_adt_type(btype):
            continue
        io_map[name] = btype
    return io_map

class ArchMapper:
    def __init__(self,
        arch_fclosure : tp.Callable,
        solver_name : str = 'z3',
        constraints = []
    ):
        self.solver_name = solver_name

        #should contain instruction as first argument
        arch_smt = arch_fclosure(SMTBitVector.get_family())
        self.smt_isa = get_isa(arch_smt)
        self.bv_isa = get_isa(arch_fclosure(BitVector.get_family()))

        self.arch_sim = arch_smt()

        self.arch_inputs = arch_smt.__call__._peak_inputs_
        self.arch_outputs = arch_smt.__call__._peak_outputs_


        #remove isa from arch_inputs list
        self.arch_inputs = _filter_adt_types(self.arch_inputs)


        def constraint_filter(inst):
            return all(constraint(inst) for constraint in constraints)
        logging.debug("Enumerating bv instructions")
        self.bv_isa_list = list(filter(constraint_filter, self.bv_isa.enumerate()))
        logging.debug("Enumerating smt instructions")
        self.smt_isa_list = list(filter(constraint_filter, self.smt_isa.enumerate()))

    def map_ir_op(self,
        ir_fclosure : tp.Callable,
        max_mappings : int = 1,
        verbose : int = 0,
    ):

        if verbose == 1:
            logging.getLogger().setLevel(logging.DEBUG)
        elif verbose == 2:
            logging.getLogger().setLevel(logging.DEBUG - 1)

        #should only contain bitvectors as inputs
        ir_smt = ir_fclosure(SMTBitVector.get_family())

        ir_inputs = ir_smt.__call__._peak_inputs_
        ir_outputs = ir_smt.__call__._peak_outputs_

        found = 0
        if found >= max_mappings:
            return
        #--------

        logging.debug("Starting search")
        ir_smt_vars = {k : v() for k,v in ir_inputs.items()}
        #This actually contains the symbolic representation
        ir_smt_expr = ir_smt()(**ir_smt_vars)
        binder = Binder(self.arch_inputs,ir_inputs,ir_smt_vars)

        for ii,smt_inst in enumerate(self.smt_isa_list):
            logging.debug(f"inst {ii+1}/{len(self.bv_isa_list)}")
            logging.debug(smt_inst)

            for bi,binding in enumerate(binder.get_bindings()):

                #enumerate possibilities for missing inputs
                for missing_inputs in binder.get_missing_inputs_list():
                    #building binding_dict
                    binding_dict,name_binding = binder.construct_binding_dict(missing_inputs,binding)
                    rvals = self.arch_sim(smt_inst, **binding_dict)
                    if not isinstance(rvals, tuple):
                        rvals = rvals,

                    for ridx, rval in enumerate(rvals):
                        assert isinstance(rval, (SMTBit, SMTBitVector))
                        assert rval.value.get_type() == ir_smt_expr.value.get_type()
                        with smt.Solver(self.solver_name, logic=QF_BV) as solver:
                            if self.check_equal(binding_dict, rval, ir_smt_expr, name_binding):
                                #Create output and input map
                                output_map = {"out":list(ir_outputs.items())[ridx][0]}
                                input_map = name_binding
                                mapping = dict(
                                    instruction=self.bv_isa_list[ii],
                                    output_map=output_map,
                                    input_map=input_map
                                )
                                yield mapping
                                found  += 1
                                if found >= max_mappings:
                                    return

    def check_equal(self, smt_vars, expr1, expr2, name_binding):
        with smt.Solver(self.solver_name, logic=QF_BV) as solver:
            expr = expr1 != expr2
            solver.add_assertion(expr.value)
            if not solver.solve():
                return True
            else:
                model = solver.get_model()
                model = {k : model[v.value] for k,v in smt_vars.items()}
                logging.log(logging.DEBUG - 1, name_binding)
                logging.log(logging.DEBUG - 1, model)
                return False
