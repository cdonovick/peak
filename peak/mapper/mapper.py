import typing as tp
import itertools as it
import functools as ft
import logging
from ..peak import Peak
import coreir
from .binding import Binder, get_from_path, binding_pretty_print
from hwtypes import AbstractBitVector
from hwtypes import BitVector, SIntVector
from hwtypes import is_adt_type
from hwtypes.adt import Product
from hwtypes import SMTBit, SMTBitVector, SMTSIntVector

import pysmt.shortcuts as smt
from pysmt.logics import QF_BV

def _tupleify(vals):
    if not isinstance(vals, tuple):
        vals = vals,
    return vals

#Will not need 'ordered_dict once hwtypes #57 is resolved
def _make_adt_instance(rvals, isa):
    rvals = _tupleify(rvals)
    rdict = {}
    for i, name in enumerate(isa.field_dict.keys()):
        rdict[name] = rvals[i]
    return isa(**rdict)

class ArchMapper:
    def __init__(self,
        arch_class : Peak,
        solver_name : str = 'z3',
        custom_enumeration : tp.Mapping[type, tp.Callable] = {}
    ):
        self.solver_name = solver_name
        self.custom_enumeration = custom_enumeration

        arch_smt = arch_class.rebind(SMTBitVector.get_family())
        self.arch_sim = arch_smt()

        self.arch_input_isa = arch_smt.get_inputs()
        self.arch_output_isa = arch_smt.get_outputs()

    def map_ir_op(self,
        ir_class : Peak,
        max_mappings : int = 1,
        verbose : int = 0,
    ):

        if verbose == 1:
            logging.getLogger().setLevel(logging.DEBUG)
        elif verbose == 2:
            logging.getLogger().setLevel(logging.DEBUG - 1)

        ir_smt = ir_class.rebind(SMTBitVector.get_family())

        ir_input_isa = ir_smt.get_inputs()
        ir_output_isa = ir_smt.get_outputs()

        found = 0
        if found >= max_mappings:
            return
        #--------

        logging.debug("Starting search")

        input_binder = Binder(
            self.arch_input_isa,
            ir_input_isa,
            allow_existential=True,
            custom_enumeration=self.custom_enumeration
        )
        output_binder = Binder(self.arch_output_isa, ir_output_isa, allow_existential=False)
        ##Early out if no bindings
        #if not (input_binder.has_binding and output_binder.has_binding):
        #    return
        for input_binding in input_binder.enumerate():

            ir_instr = input_binder.ir_instr
            ir_rvals = ir_smt()(**ir_instr.value_dict)
            ir_output_instr = _make_adt_instance(ir_rvals, ir_output_isa)

            #In the future we can use SMT for some of the variables instead of enumerating
            for arch_instr, input_binding in input_binder.enumerate_binding(input_binding):
                arch_rvals = (self.arch_sim(**arch_instr.value_dict))
                arch_output_instr = _make_adt_instance(arch_rvals, self.arch_output_isa)
                for output_binding in output_binder.enumerate():
                    output_binding = list(output_binding)
                    mapping_found = True
                    for ir_path, arch_path in output_binding:
                        if not isinstance(ir_path, tuple):
                            continue
                        ir_val = get_from_path(ir_output_instr, ir_path)
                        arch_val = get_from_path(arch_output_instr, arch_path)

                        mapping_found &= self.smt_check_equal(ir_val, arch_val)
                    if mapping_found:
                        mapping = dict(
                            input_binding=input_binding,
                            output_binding=output_binding
                        )
                        yield mapping
                        found  += 1
                        if found >= max_mappings:
                            return


    def smt_check_equal(self, expr1, expr2):
        with smt.Solver(self.solver_name, logic=QF_BV) as solver:
            expr = expr1 != expr2
            solver.add_assertion(expr.value)
            if not solver.solve():
                return True
            else:
                return False
