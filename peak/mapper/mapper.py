import typing as tp
import itertools as it
from peak import Peak
from hwtypes.adt import Product
from hwtypes import SMTBit
from hwtypes import SMTBitVector as SBV
from hwtypes import Bit, BitVector
from peak.assembler import Assembler, AssembledADT
from .utils import SMTForms, SimplifyBinding
from .utils import Unbound, Match
from .utils import create_bindings
from .utils import aadt_product_to_dict
from .utils import solved_to_bv, log2
from .utils import smt_binding_to_bv_binding
from .utils import pretty_print_binding

import pysmt.shortcuts as smt
from pysmt.logics import BV
from collections import OrderedDict

import operator
from functools import partial, reduce

or_reduce = partial(reduce, operator.or_)
and_reduce = partial(reduce, operator.and_)

class SMTMapper:
    def __init__(self, peak_fc : tp.Callable):
        if not (hasattr(peak_fc,"_is_fc") and peak_fc._is_fc):
            raise ValueError(f"family closure {peak_fc} needs to be decorated with @family_closure")
        Peak_cls = peak_fc(SMTBit.get_family())
        input_t = Peak_cls.input_t
        output_t = Peak_cls.output_t
        input_aadt_t = AssembledADT[input_t, Assembler, SBV]
        output_aadt_t = AssembledADT[output_t, Assembler, SBV]

        input_forms, input_varmap = SMTForms()(input_aadt_t)

        #output_form = output_forms[input_form_idx][output_form_idx]
        output_forms = []
        for input_form in input_forms:
            inputs = aadt_product_to_dict(input_form.value)

            #Construct output_aadt value
            output = Peak_cls()(**inputs)
            if isinstance(output,tuple):
                ofields = {field:output[i] for i, field in enumerate(output_aadt_t.adt_t.field_dict)}
            else:
                ofields = {field:output for field in output_aadt_t.adt_t.field_dict}
            output = output_aadt_t.from_fields(**ofields)

            forms, output_varmap = SMTForms()(output_aadt_t, value=output)
            #Check consistency of SMTForms
            for f in forms:
                assert f.value == output
            output_forms.append(forms)
        num_input_forms = len(output_forms)
        num_output_forms = len(output_forms[0])

        #verify same number of output forms
        assert all(num_output_forms == len(forms) for forms in output_forms)
        self.peak_fc = peak_fc

        self.input_form_var = SBV[num_input_forms]()
        self.output_form_var = SBV[num_output_forms]()

        self.input_forms = input_forms
        self.output_forms = output_forms
        self.num_output_forms = num_output_forms
        self.num_input_forms = num_input_forms
        self.input_varmap = input_varmap


class ArchMapper(SMTMapper):
    def __init__(self, arch_fc):
        super().__init__(arch_fc)
        if self.num_output_forms > 1:
            raise NotImplementedError("NYI, multiple ir output forms")

    def process_ir_instruction(self, ir_fc):
        return IRMapper(self, ir_fc)

class IRMapper(SMTMapper):
    def __init__(self, archmapper, ir_fc):
        super().__init__(ir_fc)
        #For now assume that ir input forms and ir output forms is just 1
        if self.num_input_forms > 1:
            raise NotImplementedError("NYI, multiple ir input forms")
        if self.num_output_forms > 1:
            raise NotImplementedError("NYI, multiple ir output forms")
        ir_input_form = self.input_forms[0]
        ir_output_form = self.output_forms[0][0]

        self.archmapper = archmapper
        arch_output_form = archmapper.output_forms[0]

        #binding = [input_form_idx][bidx]
        input_bindings = [create_bindings(af.varmap, ir_input_form.varmap) for af in archmapper.input_forms]

        #binding = [bidx]
        output_bindings = create_bindings(archmapper.output_forms[0][0].varmap, ir_output_form.varmap)
        form_var = archmapper.input_form_var

        #Create the form_conditions (preconditions) based off of the arch_forms
        #[input_form_idx]
        form_conditions = []
        for fi, form in enumerate(archmapper.input_forms):
            #form_condition represents the & of all the appropriate matche
            conditions = [form_var == 2**fi]
            for path, choice in form.path_dict.items():
                match_path = path + (Match, )
                assert match_path in archmapper.input_varmap
                conditions.append(archmapper.input_varmap[match_path][choice])
            form_conditions.append(conditions)


        max_input_bindings = max(len(bindings) for bindings in input_bindings)
        ib_var = SBV[max_input_bindings]()
        max_output_bindings = len(output_bindings)
        ob_var = SBV[max_output_bindings]()

        constraints = []
        #Build the constraint
        for fi, ibindings in enumerate(input_bindings):
            conditions = list(form_conditions[fi])
            for bi, ibinding in enumerate(ibindings):
                bi_match = (ib_var == 2**bi)
                #Build substitution map
                submap = []
                for ir_path, arch_path in ibinding:
                    if ir_path is Unbound:
                        continue
                    ir_var = self.input_varmap[ir_path]
                    arch_var = archmapper.input_varmap[arch_path]
                    submap.append((arch_var, ir_var))

                for bo, obinding in enumerate(output_bindings):
                    bo_match = (ob_var == 2**bo)
                    conditions = list(form_conditions[fi]) + [bi_match, bo_match]
                    for ir_path, arch_path in obinding:
                        if ir_path is Unbound:
                            continue
                        ir_out = self.output_forms[0][0].varmap[ir_path]
                        arch_out = archmapper.output_forms[fi][0].varmap[arch_path]
                        arch_out = arch_out.substitute(*submap)
                        conditions.append(ir_out == arch_out)
                    constraints.append(conditions)

        formula = or_reduce([and_reduce(conds) for conds in constraints])
        forall_vars = [var.value for var in self.input_varmap.values()]

        self.ib_var = ib_var
        self.ob_var = ob_var
        self.input_bindings = input_bindings
        self.output_bindings = output_bindings
        self.formula = smt.ForAll(forall_vars, formula.value)

    def solve(self,
        solver_name : str = 'z3',
        custom_enumeration : tp.Mapping[type, tp.Callable] = {}
    ):
        with smt.Solver(solver_name, logic=BV) as solver:
            solver.add_assertion(self.formula)
            is_solved = solver.solve()
            return MapperSolution(is_solved, solver, self)

def _bv_input_aadt_t(fc):
    bv = fc(Bit.get_family())
    input_aadt_t = AssembledADT[bv.input_t, Assembler, BitVector]
    return input_aadt_t

class MapperSolution:
    def __init__(self, is_solved, solver, irmapper):
        self.solved = is_solved
        if not is_solved:
            return
        im = irmapper
        am = irmapper.archmapper

        arch_input_form_val = log2(int(solved_to_bv(am.input_form_var, solver)))
        ib_val = log2(int(solved_to_bv(im.ib_var, solver)))
        ob_val = log2(int(solved_to_bv(im.ob_var, solver)))

        ibinding = im.input_bindings[arch_input_form_val][ib_val]
        obinding = im.output_bindings[ob_val]

        #extract, simplify, and convert constants to BV in the input binding 
        bv_ibinding = []
        #Contains all the ir paths that are bound to arch paths
        ir_bounded = set()
        for ir_path, arch_path in ibinding:
            if ir_path is Unbound:
                var = am.input_varmap[arch_path]
                bv_val = solved_to_bv(var, solver)
                ir_path = bv_val
            else:
                ir_bounded.add(ir_path)
            bv_ibinding.append((ir_path, arch_path))

        bv_ibinding = smt_binding_to_bv_binding(bv_ibinding)

        arch_input_aadt_t = _bv_input_aadt_t(am.peak_fc)

        bv_ibinding = SimplifyBinding()(arch_input_aadt_t, bv_ibinding)
        bv_ibinding = _strip_aadt(bv_ibinding)

        self.ibinding = bv_ibinding
        self.obinding = obinding
        self.ir_bounded = ir_bounded

        self.im = im
        self.am = am

    def build_ir_input(self, ir_inputs : tp.Mapping["path", BitVector]):
        ir_binding = [(val, path) for path, val in ir_inputs.items()]

        ir_input_aadt_t = _bv_input_aadt_t(self.im.peak_fc)
        complete_binding = SimplifyBinding()(ir_input_aadt_t, ir_binding)
        #internally verify entire binding was simplified to a constant
        assert len(complete_binding)==1
        assert complete_binding[0][1] is ()
        input_val = complete_binding[0][0]

        #create dict of input values
        return aadt_product_to_dict(input_val)

    def build_arch_input(self, ir_inputs : tp.Mapping["path", BitVector]):
        arch_bindings = {}
        complete_binding = []
        for ir_path, arch_path in self.ibinding:
            if isinstance(ir_path, tuple):
                if ir_path not in ir_inputs:
                    raise ValueError(f"{ir_path} must be in ir_inputs")
                complete_binding.append((ir_inputs[ir_path], arch_path))
            else:
                complete_binding.append((ir_path, arch_path))
        arch_input_aadt_t = _bv_input_aadt_t(self.am.peak_fc)
        complete_binding = SimplifyBinding()(arch_input_aadt_t, complete_binding)
        #internally verify entire binding was simplified to a constant
        assert len(complete_binding)==1
        assert complete_binding[0][1] is ()
        input_val = complete_binding[0][0]

        #create dict of input values
        return aadt_product_to_dict(input_val)

def _strip_aadt(binding):
    ret_binding = []
    for ir_path, arch_path in binding:
        if isinstance(ir_path, AssembledADT):
            ir_path = ir_path._value_
        ret_binding.append((ir_path, arch_path))
    return ret_binding
