import typing as tp
import itertools as it
from peak import family_closure, Const
from hwtypes.adt import Product, Tuple
from hwtypes import SMTBit
from hwtypes import SMTBitVector as SBV
from hwtypes import Bit, BitVector
from hwtypes.modifiers import strip_modifiers, push_modifiers, wrap_modifier, unwrap_modifier
from peak.assembler import Assembler, AssembledADT
from .utils import SMTForms, SimplifyBinding
from .utils import Unbound, Match
from .utils import create_bindings
from .utils import aadt_product_to_dict
from .utils import solved_to_bv, log2
from .utils import smt_binding_to_bv_binding
from .utils import pretty_print_binding
from hwtypes.adt_meta import GetitemSyntax, AttrSyntax, EnumMeta
import inspect
from peak import Peak

import pysmt.shortcuts as smt
from pysmt.logics import BV
from collections import OrderedDict

import operator
from functools import partial, reduce

or_reduce = partial(reduce, operator.or_)
and_reduce = partial(reduce, operator.and_)


#Helper function to search for the one peak class
def _get_peak_cls(fc_out):
    clss = []
    if not isinstance(fc_out, tuple):
        fc_out = (fc_out,)
    for cls in fc_out:
        if inspect.isclass(cls) and issubclass(cls, Peak):
            clss.append(cls)
    if len(clss) == 1:
        return clss[0]
    raise ValueError(f"Need to return one Peak class instead of {len(clss)} Peak classes: {fc_out}")

class SMTMapper:
    def __init__(self, peak_fc : tp.Callable):
        if not isinstance(peak_fc, family_closure):
            raise ValueError(f"family closure {peak_fc} needs to be decorated with @family_closure")
        Peak_cls = _get_peak_cls(peak_fc(SMTBit.get_family()))
        try:
            input_t = Peak_cls.input_t
            output_t = Peak_cls.output_t
        except AttributeError:
            raise ValueError("Need to use gen_input_t and gen_output_t")
        stripped_input_t = strip_modifiers(input_t)
        stripped_output_t = strip_modifiers(output_t)
        input_aadt_t = AssembledADT[stripped_input_t, Assembler, SBV]
        output_aadt_t = AssembledADT[stripped_output_t, Assembler, SBV]

        input_forms, input_varmap = SMTForms()(input_aadt_t)

        #output_form = output_forms[input_form_idx][output_form_idx]
        output_forms = []
        for input_form in input_forms:
            inputs = aadt_product_to_dict(input_form.value)

            #Construct output_aadt value
            outputs = Peak_cls()(**inputs)
            if not isinstance(outputs, tuple):
                outputs = (outputs,)
            if issubclass(stripped_output_t, Product):
                ofields = {field:outputs[i] for i, field in enumerate(output_aadt_t.adt_t.field_dict)}
                output_value = output_aadt_t.from_fields(**ofields)
            else:
                assert issubclass(stripped_output_t, Tuple)
                output_value = output_aadt_t.from_fields(*outputs)

            forms, output_varmap = SMTForms()(output_aadt_t, value=output_value)
            #Check consistency of SMTForms
            for f in forms:
                assert f.value == output_value
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
    def __init__(self, arch_fc, *, constrain_constant_bv=None, set_unbound_bv=None):
        super().__init__(arch_fc)
        if self.num_output_forms > 1:
            raise NotImplementedError("Multiple ir output forms")
        self.constrain_constant_bv = constrain_constant_bv
        self.set_unbound_bv = set_unbound_bv

    def process_ir_instruction(self, ir_fc):
        return IRMapper(self, ir_fc)


#Return a map from clean path to modified types
def _create_flat_map(adt_t, path=(), mods=[]):
    #remove modifiers from this level
    adt_t, new_mods = unwrap_modifier(adt_t)
    mods = new_mods + mods
    flatmap = {}
    if isinstance(adt_t, (AttrSyntax, GetitemSyntax)) and not isinstance(adt_t, EnumMeta):
        for n, sub_adt_t in adt_t.field_dict.items():
            sub_flatmap = _create_flat_map(sub_adt_t, path+(n,), mods)
            flatmap.update(sub_flatmap)
    else:
        flatmap[path] = wrap_modifier(adt_t, mods)
    return flatmap


class IRMapper(SMTMapper):
    def __init__(self, archmapper, ir_fc):
        super().__init__(ir_fc)
        #For now assume that ir input forms and ir output forms is just 1
        if self.num_input_forms > 1:
            raise NotImplementedError("Multiple ir input forms")
        if self.num_output_forms > 1:
            raise NotImplementedError("Multiple ir output forms")
        ir_input_form = self.input_forms[0]
        ir_output_form = self.output_forms[0][0]

        self.archmapper = archmapper
        arch_output_form = archmapper.output_forms[0]

        # Create input bindings
        # binding = [input_form_idx][bidx]
        input_bindings = []
        arch_input_flat_map = _create_flat_map(archmapper.peak_fc(SMTBit.get_family()).input_t)

        ir_flat_map = _create_flat_map(self.peak_fc(SMTBit.get_family()).input_t)
        #Verify all paths are the same
        assert set(ir_flat_map.keys()) == set(self.input_varmap.keys())
        for af in archmapper.input_forms:
            #Verify all paths of form is subset of all paths
            assert set(arch_input_flat_map.keys()).issuperset(set(af.varmap.keys()))
            form_arch_input_flat_map = {p:T for p, T in arch_input_flat_map.items() if p in af.varmap}
            input_bindings.append(create_bindings(form_arch_input_flat_map, ir_flat_map))
        # Check Early out
        self.has_bindings = max(len(bs) for bs in input_bindings) > 0
        if not self.has_bindings:
            return

        # Create output bindings
        arch_output_flat_map = _create_flat_map(archmapper.peak_fc(SMTBit.get_family()).output_t)
        ir_flat_map = _create_flat_map(self.peak_fc(SMTBit.get_family()).output_t)

        #binding = [bidx]
        output_bindings = create_bindings(arch_output_flat_map, ir_flat_map)

        # Check Early out
        self.has_bindings = len(output_bindings) > 0
        if not self.has_bindings:
            return

        form_var = archmapper.input_form_var
        #Create the form_conditions (preconditions) based off of the arch_forms
        #[input_form_idx]
        form_conditions = []
        for fi, form in enumerate(archmapper.input_forms):
            #form_condition represents the & of all the appropriate matche
            conditions = [form_var == 2**fi]
            for path, choice in form.path_dict.items():
                match_path = path + (Match,)
                assert match_path in archmapper.input_varmap
                conditions.append(archmapper.input_varmap[match_path][choice])
            form_conditions.append(conditions)


        max_input_bindings = max(len(bindings) for bindings in input_bindings)
        ib_var = SBV[max_input_bindings]()
        max_output_bindings = len(output_bindings)
        ob_var = SBV[max_output_bindings]()


        def check_constrain_constant_bv(ir_path, arch_path):
            is_en = archmapper.constrain_constant_bv is not None
            is_unbound = ir_path is Unbound
            arch_t = arch_input_flat_map[arch_path]
            is_const = issubclass(arch_t, Const)
            is_bv = issubclass(arch_t, SBV)
            ret = is_en and is_unbound and is_const and is_bv
            return ret

        def check_set_unbound_bv(ir_path, arch_path):
            is_en = archmapper.set_unbound_bv is not None
            is_unbound = ir_path is Unbound
            arch_t = arch_input_flat_map[arch_path]
            is_not_const = not issubclass(arch_t, Const)
            is_bv = issubclass(arch_t, SBV)
            ret = is_en and is_unbound and is_not_const and is_bv
            return ret

        constraints = []
        #Build the constraint
        for fi, ibindings in enumerate(input_bindings):
            conditions = list(form_conditions[fi])
            for bi, ibinding in enumerate(ibindings):
                bi_match = (ib_var == 2**bi)
                #Build substitution map
                submap = []
                const_constraints = []
                for ir_path, arch_path in ibinding:
                    #if ir_path is Unbound:
                    #    continue
                    #ir_var = self.input_varmap[ir_path]
                    #arch_var = archmapper.input_varmap[arch_path]
                    arch_var = archmapper.input_varmap[arch_path]
                    if check_set_unbound_bv(ir_path, arch_path):
                        #replace the arch_value with a constant
                        ir_var = type(arch_var)(archmapper.set_unbound_bv)
                        assert 0
                    elif check_constrain_constant_bv(ir_path, arch_path):
                        width = arch_var.size
                        const_constraint = or_reduce((arch_var == val for val in archmapper.constrain_constant_bv if val < 2**width))
                        const_constraints.append(const_constraint)
                        continue

                    elif ir_path is Unbound:
                        continue
                    else:
                        ir_var = self.input_varmap[ir_path]

                    submap.append((arch_var, ir_var))
                for bo, obinding in enumerate(output_bindings):
                    bo_match = (ob_var == 2**bo)
                    conditions = list(form_conditions[fi]) + [bi_match, bo_match] + const_constraints
                    #conditions = list(form_conditions[fi]) + [bi_match, bo_match]
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
        if not self.has_bindings:
            return MapperSolution(False, None, None)

        with smt.Solver(solver_name, logic=BV) as solver:
            solver.add_assertion(self.formula)
            is_solved = solver.solve()
            return MapperSolution(is_solved, solver, self)

def _bv_input_aadt_t(fc):
    bv = fc(Bit.get_family())
    input_aadt_t = AssembledADT[strip_modifiers(bv.input_t), Assembler, BitVector]
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
