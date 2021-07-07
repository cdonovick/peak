import typing as tp
from peak import family_closure, Const
from hwtypes.adt import Product, Tuple
from hwtypes import Bit, BitVector
from hwtypes import AbstractBit, AbstractBitVector
from hwtypes.adt import is_adt_type
from hwtypes.modifiers import strip_modifiers, wrap_modifier, unwrap_modifier
from peak.assembler import Assembler, AssembledADT
from .utils import SMTForms, SimplifyBinding
from .utils import Unbound, Match
from .utils import create_bindings, pretty_print_binding
from .utils import aadt_product_to_dict
from .utils import solved_to_bv, log2
from .utils import rebind_binding
from .utils import rebind_type
from hwtypes.adt_meta import GetitemSyntax, AttrSyntax, EnumMeta
import inspect
from peak import Peak
from peak import family as peak_family
import logging
logger = logging.getLogger(__name__)

import pysmt.shortcuts as smt
from pysmt.logics import BV

import operator
from functools import partial, reduce, lru_cache

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


# Wraps the oututs to be of type output_t
def wrap_outputs(outputs, output_aadt):
    output_t = output_aadt.adt_t
    if not isinstance(outputs, tuple):
        outputs = (outputs,)
    if issubclass(output_t, Product):
        ofields = {field:outputs[i] for i, field in enumerate(output_aadt.adt_t.field_dict)}
        return output_aadt.from_fields(**ofields)
    else:
        assert issubclass(output_t, Tuple)
        return output_aadt.from_fields(*outputs)

#Return a map from clean path to modified types
def _create_path_to_adt(adt_t, path=(), mods=[]):
    #remove modifiers from this level
    adt_t, new_mods = unwrap_modifier(adt_t)
    mods = new_mods + mods
    flatmap = {}
    if isinstance(adt_t, (AttrSyntax, GetitemSyntax)) and not isinstance(adt_t, EnumMeta):
        for n, sub_adt_t in adt_t.field_dict.items():
            sub_flatmap = _create_path_to_adt(sub_adt_t, path+(n,), mods)
            flatmap.update(sub_flatmap)
    else:
        flatmap[path] = wrap_modifier(adt_t, mods)
    return flatmap

class SMTMapper:
    def __init__(self, peak_fc : tp.Callable, family=peak_family):
        self.family = family
        if not isinstance(peak_fc, family_closure):
            raise ValueError(f"family closure {peak_fc} needs to be decorated with @family_closure")
        Peak_cls = _get_peak_cls(peak_fc(family.SMTFamily()))
        name = Peak_cls.__name__
        try:
            input_t = Peak_cls.input_t
            output_t = Peak_cls.output_t
        except AttributeError:
            raise ValueError("Need to use gen_input_t and gen_output_t")
        stripped_input_t = strip_modifiers(input_t)
        stripped_output_t = strip_modifiers(output_t)
        input_aadt_t = family.SMTFamily().get_adt_t(stripped_input_t)
        self.input_aadt_t = input_aadt_t
        output_aadt_t = family.SMTFamily().get_adt_t(stripped_output_t)
        self.output_aadt_t = output_aadt_t
        input_forms, input_varmap, input_value = SMTForms()(input_aadt_t)
        self.input_value = input_value
        #output_form = output_forms[input_form_idx][output_form_idx]
        output_forms = []
        self.const_valid_conditions = []
        const_fields = [field for field, T in input_t.field_dict.items() if issubclass(T, Const)]

        for input_form in input_forms:
            inputs = aadt_product_to_dict(input_form.value)
            self.const_valid_conditions.append([is_valid(inputs[field]) for field in const_fields])
            #Construct output_aadt value
            outputs = Peak_cls()(**inputs)
            output_value = wrap_outputs(outputs, output_aadt_t)

            forms, output_varmap, _ = SMTForms()(output_aadt_t, value=output_value)
            #Check consistency of SMTForms
            for f in forms:
                assert f.value == output_value
            output_forms.append(forms)
        num_input_forms = len(output_forms)
        num_output_forms = len(output_forms[0])

        #verify same number of output forms
        assert all(num_output_forms == len(forms) for forms in output_forms)
        self.peak_fc = peak_fc
        SBV = family.SMTFamily().BitVector
        self.input_form_var = SBV[num_input_forms](prefix=f"{name}_if")
        self.output_form_var = SBV[num_output_forms](prefix=f"{name}_of")

        self.input_forms = input_forms
        self.output_forms = output_forms
        self.num_output_forms = num_output_forms
        self.num_input_forms = num_input_forms
        self.input_varmap = input_varmap
        self.const_paths = set(path for path, T in self.path_to_adt(True, strip=False).items() if issubclass(T, Const))

    @lru_cache(None)
    def path_to_adt(self, input, strip=False):
        cls = self.peak_fc.Py
        adt = cls.input_t if input else cls.output_t
        if strip:
            adt = strip_modifiers(adt)
        return _create_path_to_adt(adt)

class ArchMapper(SMTMapper):
    def __init__(self, arch_fc, *, path_constraints= {}, family=peak_family):
        super().__init__(arch_fc, family=family)
        if self.num_output_forms > 1:
            raise NotImplementedError("Multiple ir output forms")

        #Verify that all the path_constraints are valid
        path_constraints = {path: (c if isinstance(c, tuple) else (c,)) for path, c in path_constraints.items()}
        path_to_adt = self.path_to_adt(input=True, strip=True)
        for path, constraints in path_constraints.copy().items():
            if path not in path_to_adt:
                raise ValueError(f"{path} is either invalid or not an adt leaf")
            assert path in self.input_varmap
            adt = path_to_adt[path]
            aadt = self.family.SMTFamily().get_adt_t(rebind_type(adt, self.family.SMTFamily()))
            try:
                constraints = tuple((aadt(c) for c in constraints))
            except Exception as e:
                print("Invalid constraints for {path}")
                raise e
            path_constraints[path] =constraints

        self.path_constraints = path_constraints

    def process_ir_instruction(self, ir_fc, simple_formula=False):
        return IRMapper(self, ir_fc, simple_formula)

def is_valid(aadt_value: tp.Union[AssembledADT, AbstractBit, AbstractBitVector]):
    if isinstance(aadt_value, (AbstractBitVector, AbstractBit)):
        return aadt_value.get_family().Bit(1)
    else:
        return type(aadt_value)._is_valid_(aadt_value._value_)

class RewriteRule:
    def __init__(self, ibinding, obinding, ir_fc, arch_fc):
        self.family = arch_fc._family_
        #Verify that there are no Unbound Consts in the ibinding
        #Force each value to be the appropriate size python bitvector
        #verify that each type is valid
        arch_path_types = _create_path_to_adt(arch_fc.Py.input_t)
        self.ibinding = []
        for ir_path, arch_path in ibinding:
            if ir_path is Unbound and isinstance(arch_path_types[arch_path], Const):
                raise ValueError(f"Arch path {arch_path} needs to have a value")
            elif ir_path is not Unbound and not isinstance(ir_path, tuple):
                #Build the python bitvector and verify it is valid
                T = strip_modifiers(arch_path_types[arch_path])
                aadt = AssembledADT[T, Assembler, self.family.PyFamily().BitVector]
                ir_path = aadt(ir_path)
                if is_adt_type(T):
                    if not is_valid(ir_path):
                        raise ValueError(f"{ir_path} is not valid for {arch_path}")
                    ir_path = ir_path._value_
                assert isinstance(ir_path, (AbstractBit, AbstractBitVector))
            self.ibinding.append((ir_path, arch_path))

        self.obinding = obinding
        self.ir_fc = ir_fc
        self.arch_fc = arch_fc

    def get_input_paths(self):
        #Input paths are ir_paths, and arch_paths which are not const and do not have a value
        arch_path_types = _create_path_to_adt(self.arch_fc(self.family.SMTFamily()).input_t)
        ir_paths = set()
        arch_paths = set()
        for ir_path, arch_path in self.ibinding:
            if isinstance(ir_path, tuple):
                ir_paths.add(ir_path)
            elif ir_path is Unbound and not isinstance(arch_path_types[arch_path], Const):
                arch_paths.add(arch_path)
        return ir_paths, arch_paths

    def build_inputs(self, ir_inputs: tp.Mapping["path", BitVector], arch_inputs: tp.Mapping["path", BitVector], family):
        ir_paths, arch_paths = self.get_input_paths()
        if set(ir_inputs.keys()) != set(ir_paths):
            raise ValueError("ir_inputs are wrong")
        if set(arch_inputs.keys()) != set(arch_paths):
            raise ValueError("arch_inputs are wrong")

        ibinding = rebind_binding(self.ibinding, family)
        ir_binding = []
        arch_binding = []
        for ir_path, arch_path in ibinding:
            if isinstance(ir_path, tuple):
                assert ir_path in ir_inputs
                val = ir_inputs[ir_path]
                ir_binding.append((val, ir_path))
                arch_binding.append((val, arch_path))
            elif ir_path is Unbound:
                assert arch_path in arch_inputs
                arch_binding.append((arch_inputs[arch_path], arch_path))
            else:
                arch_binding.append((ir_path, arch_path))

        arch_aadt = _input_aadt_t(self.arch_fc, family)
        arch_binding = SimplifyBinding()(arch_aadt, arch_binding)
        # internally verify entire binding was simplified to a constant
        assert len(arch_binding) == 1
        assert arch_binding[0][1] == ()
        arch_input = arch_binding[0][0]

        ir_aadt = _input_aadt_t(self.ir_fc, family)
        ir_binding = SimplifyBinding()(ir_aadt, ir_binding)
        #internally verify entire binding was simplified to a constant
        assert len(ir_binding)==1
        assert ir_binding[0][1] == ()
        ir_input = ir_binding[0][0]

        #create dict of input values
        return aadt_product_to_dict(ir_input), aadt_product_to_dict(arch_input)

    def parse_ir_output(self, outputs):
        output_t = self.ir_fc(self.family.SMTFamily()).output_t
        output_aadt = self.family.SMTFamily().get_adt_t(output_t)
        output_value = wrap_outputs(outputs, output_aadt)
        _, values, _ = SMTForms()(output_aadt, value=output_value)
        return values

    def parse_arch_output(self, outputs):
        output_t = self.arch_fc(self.family.SMTFamily()).output_t
        output_aadt = self.family.SMTFamily().get_adt_t(output_t)
        output_value = wrap_outputs(outputs, output_aadt)
        _, values, _ = SMTForms()(output_aadt, value=output_value)
        return values

    # Returns a counterexample if found, otherwise None
    def verify(self, solver_name: str = "z3") -> tp.Union[None, "CounterExample"]:
        # create free variable for each ir_val
        # The types are all Py
        ir_path_types = _create_path_to_adt(strip_modifiers(self.ir_fc(self.family.SMTFamily()).input_t))
        arch_path_types = _create_path_to_adt(strip_modifiers(self.arch_fc(self.family.SMTFamily()).input_t))
        ir_paths, arch_paths = self.get_input_paths()

        ir_values = {path:_free_var_from_t(ir_path_types[path], self.family) for path in ir_paths}
        arch_values = {path: _free_var_from_t(arch_path_types[path], self.family) for path in arch_paths}
        ir_inputs, arch_inputs = self.build_inputs(ir_values, arch_values, self.family.SMTFamily())
        ir = self.ir_fc(self.family.SMTFamily())()
        arch = self.arch_fc(self.family.SMTFamily())()
        ir_out_values = self.parse_ir_output(ir(**ir_inputs))
        arch_out_values = self.parse_arch_output(arch(**arch_inputs))

        outputs = []
        for ir_path, arch_path in self.obinding:
            # The value of an unused output does not matter
            if ir_path is Unbound:
                continue

            if ir_path not in ir_out_values:
                raise ValueError(f"{ir_path} is not valid")
            if arch_path not in arch_out_values:
                raise ValueError(f"{arch_path} is not valid")
            outputs.append(ir_out_values[ir_path] != arch_out_values[arch_path])
        formula = or_reduce(outputs)
        with smt.Solver(solver_name, logic=BV) as solver:
            solver.add_assertion(formula.value)
            verified = not solver.solve()
            if verified:
                return None
            else:
                ir_ce = {path: solved_to_bv(var, solver) for path, var in ir_values.items()}
                arch_ce = {path: solved_to_bv(var, solver) for path, var in arch_values.items()}
                return ir_ce, arch_ce

    def serialize_bindings(self):
        rrule_out = {}
        rrule_out["ibinding"] = []
        for t in self.ibinding:
            if isinstance(t[0], BitVector):
                rrule_out["ibinding"].append(tuple([{'type':'BitVector', 'width':len(t[0]), 'value':t[0].value}, t[1]]))
            elif isinstance(t[0], Bit):
                rrule_out["ibinding"].append(tuple([{'type':'Bit', 'width':1, 'value':t[0]._value}, t[1]]))
            elif t[0] == Unbound:
                rrule_out["ibinding"].append(tuple(["unbound", t[1]]))
            else:
                rrule_out["ibinding"].append(t)

        rrule_out["obinding"] = []
        for t in self.obinding:
            if t[0] == Unbound:
                rrule_out["obinding"].append(tuple(["unbound", t[1]]))
            else:
                rrule_out["obinding"].append(t)

        return rrule_out

def read_serialized_bindings(serialized_rr, ir_fc, arch_fc):

    input_binding = []
    output_binding = []

    for i in serialized_rr["ibinding"]:
        if isinstance(i[0], dict):
            u = i[0]
            v = i[1]
            if u['type'] == "BitVector":
                u = (BitVector[u['width']](u['value']))
            elif u['type'] == "Bit":
                u = (Bit(u['value']))

            input_binding.append(tuple([u, tuple(v) ])) 
        elif i[0] == "unbound":
            input_binding.append(tuple([Unbound, tuple(i[1])]))
        else:
            input_binding.append(tuple([tuple(i[0]), tuple(i[1])]))
            
    for o in serialized_rr["obinding"]:
        if o[0] == "unbound":
            output_binding.append(tuple([Unbound, tuple(o[1])]))
        else:
            output_binding.append(tuple([tuple(o[0]), tuple(o[1])]))

    return RewriteRule(input_binding, output_binding, ir_fc, arch_fc)


#T is always a Py type
def _free_var_from_t(T, family):
    T = rebind_type(T, family.SMTFamily())
    if issubclass(T, (family.SMTFamily().BitVector, family.SMTFamily().Bit)):
        return T()
    aadt_t = family.SMTFamily().get_adt_t(T)
    adt_t, assembler_t, bv_t = aadt_t.fields
    assembler = assembler_t(adt_t)
    return bv_t[assembler.width]()


class IRMapper(SMTMapper):
    def __init__(self, archmapper, ir_fc, simple_formula=True):
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
        arch_input_path_to_adt = archmapper.path_to_adt(input=True)

        #Removes any invalid bindings
        def constraint_filter(binding):
            for ir_path, arch_path in binding:
                if arch_path in archmapper.path_constraints and ir_path is not Unbound:
                    return False
            return True

        ir_path_to_adt = self.path_to_adt(input=True)
        #Verify all paths are the same
        assert set(ir_path_to_adt.keys()) == set(self.input_varmap.keys())
        for af in archmapper.input_forms:
            #Verify all paths of form is subset of all paths
            assert set(arch_input_path_to_adt.keys()).issuperset(set(af.varmap.keys()))
            form_arch_input_path_to_adt = {p:T for p, T in arch_input_path_to_adt.items() if p in af.varmap}
            bindings = create_bindings(form_arch_input_path_to_adt, ir_path_to_adt)
            bindings = list(filter(constraint_filter, bindings))
            for i, b in enumerate(bindings):
                logger.debug(f"Binding {i}")
                pretty_print_binding(b, logger.debug)
            input_bindings.append(bindings)
        # Check Early out
        self.has_bindings = max(len(bs) for bs in input_bindings) > 0
        if not self.has_bindings:
            logger.debug("Early out, no input binidngs")
            return

        # Create output bindings
        arch_output_path_to_adt = archmapper.path_to_adt(input=False)
        ir_path_to_adt = self.path_to_adt(input=False)

        #binding = [bidx]
        output_bindings = create_bindings(arch_output_path_to_adt, ir_path_to_adt)

        # Check Early out
        self.has_bindings = len(output_bindings) > 0
        if not self.has_bindings:
            logger.debug("Early out, no output binidngs")
            return

        form_var = archmapper.input_form_var


        #Create the form_conditions (preconditions) based off of the arch_forms
        #[input_form_idx]
        form_conditions = []
        for fi, form in enumerate(archmapper.input_forms):
            # form_condition represents the & of all the appropriate matches
            #   and that the const adt types are valid
            assert len(archmapper.const_valid_conditions[fi]) > 0
            conditions = [form_var == 2**fi] + archmapper.const_valid_conditions[fi]
            for path, choice in form.path_dict.items():
                match_path = path + (Match,)
                assert match_path in archmapper.input_varmap
                conditions.append(archmapper.input_varmap[match_path][choice])
            form_conditions.append(conditions)


        max_input_bindings = max(len(bindings) for bindings in input_bindings)
        SBV = self.family.SMTFamily().BitVector
        ib_var = SBV[max_input_bindings](prefix="ib")
        max_output_bindings = len(output_bindings)
        ob_var = SBV[max_output_bindings](prefix="ob")

        self.ib_var = ib_var
        self.ob_var = ob_var
        self.input_bindings = input_bindings
        self.output_bindings = output_bindings


        #--------------------------------------------
        if simple_formula:
            #TODO these are wrong once the Exists intersect FOrall issue shows up
            const_fields = [field for field, T in archmapper.peak_fc.Py.input_t.field_dict.items() if issubclass(T, Const)]
            inputs = aadt_product_to_dict(archmapper.input_value)
            const_valid_conditions = [is_valid(inputs[field]) for field in const_fields]
            preconditions = [and_reduce(const_valid_conditions)]

            #Alternative correct (but slower) precondition
            #preconditions = [is_valid(archmapper.input_value), is_valid(self.input_value)]

            # Create the form_conditions (preconditions) based off of the arch_forms
            # [input_form_idx]
            form_conditions = []
            for fi, form in enumerate(archmapper.input_forms):
                conditions = [form_var == 2**fi]
                for path, choice in form.path_dict.items():
                    match_path = path + (Match,)
                    assert match_path in archmapper.input_varmap
                    conditions.append(archmapper.input_varmap[match_path][choice])
                form_conditions.append(and_reduce(conditions))
            preconditions.append(or_reduce(form_conditions))

            #Alternate formula construction
            #indexed by (fi, bi)
            forall_vars_dict = {}
            exists_vars_dict = {}
            fb_conditions = {} #form/binding conditions in a list
            for fi, ibindings in enumerate(input_bindings):
                fi_conditions = [form_var==2**fi]
                for bi, ibinding in enumerate(ibindings):
                    forall_vars = {}
                    exists_vars = {}
                    conditions = fi_conditions + [(ib_var == 2 ** bi)]
                    for ir_path, arch_path in ibinding:
                        arch_name = ".".join(["A"] + [str(p) for p in arch_path])
                        arch_var = archmapper.input_varmap[arch_path]
                        is_unbound = ir_path is Unbound
                        is_constrained = arch_path in self.archmapper.path_constraints
                        is_const = issubclass(arch_input_path_to_adt[arch_path], Const)
                        if is_constrained:
                            if not is_unbound:
                                raise NotImplementedError()
                        if is_unbound and not is_const:
                            forall_vars[arch_name] = arch_var
                        elif is_unbound and is_const:
                            exists_vars[arch_name] = arch_var
                        elif not is_unbound:
                            assert not is_unbound
                            ir_name = ".".join(["I"] + [str(p) for p in ir_path])
                            ir_var = self.input_varmap[ir_path]
                            forall_vars[arch_name] = arch_var
                            forall_vars[ir_name] = ir_var
                            conditions.append(arch_var==ir_var)
                    forall_vars_dict[(fi, bi)] = forall_vars
                    exists_vars_dict[(fi, bi)] = exists_vars
                    fb_conditions[(fi, bi)] = conditions

            # Check if there is any overlap between forall_vars and exist vars
            foralls = set([name for vars in forall_vars_dict.values() for name in vars])
            exists = set([name for vars in exists_vars_dict.values() for name in vars])
            if len(foralls.intersection(exists)) > 0:
                raise NotImplementedError()
                #Will need to do an input transformation

            pysmt_forall_vars = set([var.value for forall_vars in forall_vars_dict.values() for var in forall_vars.values()])

            #Create F
            def run_peak(mapper):
                obj = mapper.peak_fc.SMT()
                input_dict = aadt_product_to_dict(mapper.input_value)
                outputs = obj(**input_dict)
                output = wrap_outputs(outputs, mapper.output_aadt_t)
                output_dict = aadt_product_to_dict(output)
                return {(k,):v for k,v in output_dict.items()}


            def impl(p, q):
                return (~p) | q
            arch_output_dict = run_peak(archmapper)
            ir_output_dict = run_peak(self)
            F_conds = []
            o_preconditions = []
            for bo, obinding in enumerate(output_bindings):
                ob_cond = (ob_var == 2**bo)
                o_conds = []
                o_preconditions.append(ob_cond)
                for ir_path, arch_path in obinding:
                    if ir_path is Unbound:
                        continue
                    ir_out = ir_output_dict[ir_path]
                    arch_out = arch_output_dict[arch_path]
                    o_conds.append(ir_out == arch_out)
                F_conds.append(impl(ob_cond, and_reduce(o_conds)))
            assert len(F_conds) > 0
            preconditions.append(or_reduce(o_preconditions))
            F = and_reduce(F_conds)
            impl_conds = []
            fb_conds = []


            logger.debug("Formula conditions")
            for (f,b), conds in fb_conditions.items():
                logger.debug(f"F{f},{b}")
                fb_conds.append((form_var == 2**f) & (ib_var == 2**b))
                logger.debug("  Forall: " + " | ".join(f"{p}->{v.value}" for p, v in forall_vars_dict[(f,b)].items()))
                for cond in conds:
                    logger.debug(f"  {cond.value.serialize()}")
                fb_cond = and_reduce(conds)
                impl_conds.append(fb_cond)

            exist_constraints = []
            forall_constraints = []
            for path, constraints in archmapper.path_constraints.items():
                is_const = issubclass(arch_input_path_to_adt[path], Const)
                arch_var = archmapper.input_varmap[path]
                if is_const:
                    exist_constraints.append(or_reduce((arch_var==c for c in constraints)))
                else:
                    forall_constraints.append(or_reduce((arch_var==c for c in constraints)))
            preconditions += exist_constraints
            preconditions.append(or_reduce(fb_conds))
            F_cond = and_reduce(forall_constraints + [or_reduce(impl_conds)])

            formula = and_reduce(preconditions) & impl(F_cond, F)
            self.formula = smt.ForAll(list(pysmt_forall_vars), formula.value)
            self.forall_vars = pysmt_forall_vars
            self.formula_wo_forall = formula.value
        else:
            constraints = []
            #Build the constraint
            forall_vars = set()
            for fi, ibindings in enumerate(input_bindings):
                conditions = list(form_conditions[fi])
                for bi, ibinding in enumerate(ibindings):
                    bi_match = (ib_var == 2**bi)
                    #Build substitution map
                    submap = []
                    for ir_path, arch_path in ibinding:
                        arch_var = archmapper.input_varmap[arch_path]
                        is_unbound = ir_path is Unbound
                        is_constrained = arch_path in self.archmapper.path_constraints
                        is_const = issubclass(arch_input_path_to_adt[arch_path], Const)
                        if is_constrained:
                            assert is_unbound
                            continue

                        if is_unbound and not is_const:
                            #add arch_var to list of forall vars
                            forall_vars.add(arch_var.value)
                        elif not is_unbound and not is_constrained:
                            #substitue arch_var with ir_var add ir_var to forall list
                            ir_var = self.input_varmap[ir_path]
                            submap.append((arch_var, ir_var))
                            forall_vars.add(ir_var.value)

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

            logger.debug("Unconstrained Formula")
            for c in constraints:
                logger.debug("  [")
                for cond in c:
                    logger.debug(f"    {cond.value},")
                logger.debug("  ],")
            formula = or_reduce([and_reduce(conds) for conds in constraints])

            # Adding in the constraints:

            # Start with the non-const constraints.
            # This is basically doing universal qualifier over a limited set of values
            #   To do this, evaluate the formula with each possible value,
            #   then 'and' together the resulting partially-evaluted formulas
            for path, constraints in archmapper.path_constraints.items():
                is_const = issubclass(arch_input_path_to_adt[path], Const)
                if is_const:
                    continue
                arch_var = archmapper.input_varmap[path]
                formula = and_reduce((formula.substitute((arch_var, c)) for c in constraints))

            # Then deal with the const constraints.
            # This is saying only allow a set of values for the existential quantifier
            # Thus just create an additional constraint that arch_var is either c1 or c2 or c3
            for path, constraints in archmapper.path_constraints.items():
                is_const = issubclass(arch_input_path_to_adt[path], Const)
                if not is_const:
                    continue
                arch_var = archmapper.input_varmap[path]
                constraint = or_reduce((arch_var == c for c in constraints))
                formula &= constraint

            self.formula = smt.ForAll(list(forall_vars), formula.value)
            self.forall_vars = forall_vars
            self.formula_wo_forall = formula.value

            logger.debug("Universally Quantified Vars")
            for var in forall_vars:
                logger.debug(f"  {var}")


    def solve(self,
        solver_name : str = 'z3',
        external_loop : bool = False,
        itr_limit = 10,
        logic = BV
    ) -> tp.Union[None, RewriteRule]:
        if not self.has_bindings:
            return None

        if external_loop:
            return external_loop_solve(self.forall_vars, self.formula_wo_forall, logic, itr_limit, solver_name, self)

        with smt.Solver(solver_name, logic=logic) as solver:
            solver.add_assertion(self.formula)
            is_solved = solver.solve()
            if not is_solved:
                return None
            return rr_from_solver(solver, self)

def _input_aadt_t(fc, family):
    bv = fc(family)
    input_aadt_t = AssembledADT[strip_modifiers(bv.input_t), Assembler, family.BitVector]
    return input_aadt_t


def rr_from_solver(solver, irmapper):
    im = irmapper
    am = irmapper.archmapper
    arch_input_form_val = log2(int(solved_to_bv(am.input_form_var, solver)))
    ib_val = log2(int(solved_to_bv(im.ib_var, solver)))
    ob_val = log2(int(solved_to_bv(im.ob_var, solver)))
    ibinding = im.input_bindings[arch_input_form_val][ib_val]
    obinding = im.output_bindings[ob_val]

    #extract, simplify, and convert constants to BV in the input binding
    bv_ibinding = []
    for ir_path, arch_path in ibinding:
        if (ir_path is Unbound) and (arch_path in am.const_paths or arch_path in am.path_constraints):
            var = am.input_varmap[arch_path]
            bv_val = solved_to_bv(var, solver)
            ir_path = bv_val
        bv_ibinding.append((ir_path, arch_path))

    fam = am.peak_fc._family_.PyFamily()
    bv_ibinding = rebind_binding(bv_ibinding, fam)
    arch_input_aadt_t = _input_aadt_t(am.peak_fc, fam)

    bv_ibinding = strip_aadt(bv_ibinding)
    logger.debug(f"(f,bi,bo)=({arch_input_form_val},{ib_val},{ob_val})")
    pretty_print_binding(bv_ibinding, logger.debug)
    return RewriteRule(bv_ibinding, obinding, im.peak_fc, am.peak_fc)

def external_loop_solve(y, phi, logic = BV, maxloops = 10, solver_name = "cvc4", irmapper = None):

    y = set(y)
    x = phi.get_free_variables() - y

    with smt.Solver (logic = logic, name = solver_name) as solver:
        solver.add_assertion(smt.Bool(True))
        loops = 0

        while maxloops is None or loops <= maxloops:
            loops += 1
            eres = solver.solve()

            if not eres:
                return None
            else:
                tau = {v: solver.get_value(v) for v in x}
                sub_phi = phi.substitute(tau).simplify()
                model = smt.get_model(smt.Not(sub_phi), solver_name = solver_name, logic = logic)

                if model is None:
                    return rr_from_solver(solver, irmapper)
                else :
                    sigma = {v: model.get_value(v) for v in y}
                    sub_phi = phi.substitute(sigma).simplify()
                    solver.add_assertion(sub_phi)
        ValueError("Unknown result in efsmt")


def strip_aadt(binding):
    ret_binding = []
    for ir_path, arch_path in binding:
        if isinstance(ir_path, AssembledADT):
            ir_path = ir_path._value_
        ret_binding.append((ir_path, arch_path))
    return ret_binding
