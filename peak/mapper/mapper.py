import typing as tp
from peak import family_closure, Const
from hwtypes.adt import Product, Tuple
from hwtypes import SMTBitVector as SBV
from hwtypes import Bit, BitVector
from hwtypes.modifiers import strip_modifiers, wrap_modifier, unwrap_modifier
from peak.assembler import Assembler, AssembledADT
from .utils import SMTForms, SimplifyBinding
from .utils import Unbound, Match
from .utils import create_bindings
from .utils import aadt_product_to_dict
from .utils import solved_to_bv, log2
from .utils import rebind_binding
from hwtypes.adt_meta import GetitemSyntax, AttrSyntax, EnumMeta
import inspect
from peak import Peak
from peak import family

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
    def __init__(self, peak_fc : tp.Callable):
        if not isinstance(peak_fc, family_closure):
            raise ValueError(f"family closure {peak_fc} needs to be decorated with @family_closure")
        Peak_cls = _get_peak_cls(peak_fc(family.SMTFamily()))
        try:
            input_t = Peak_cls.input_t
            output_t = Peak_cls.output_t
        except AttributeError:
            raise ValueError("Need to use gen_input_t and gen_output_t")
        stripped_input_t = strip_modifiers(input_t)
        stripped_output_t = strip_modifiers(output_t)
        input_aadt_t = family.SMTFamily().get_adt_t(stripped_input_t)
        output_aadt_t = family.SMTFamily().get_adt_t(stripped_output_t)

        input_forms, input_varmap = SMTForms()(input_aadt_t)

        #output_form = output_forms[input_form_idx][output_form_idx]
        output_forms = []
        for input_form in input_forms:
            inputs = aadt_product_to_dict(input_form.value)

            #Construct output_aadt value
            outputs = Peak_cls()(**inputs)
            output_value = wrap_outputs(outputs, output_aadt_t)

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

    @lru_cache(None)
    def path_to_adt(self, input, family, strip=False):
        cls = self.peak_fc(family)
        adt = cls.input_t if input else cls.output_t
        if strip:
            adt = strip_modifiers(adt)
        return _create_path_to_adt(adt)

class ArchMapper(SMTMapper):
    def __init__(self, arch_fc, *, path_constraints= {}):
        super().__init__(arch_fc)
        if self.num_output_forms > 1:
            raise NotImplementedError("Multiple ir output forms")

        #Verify that all the path_constraints are valid
        path_constraints = {path: (c if isinstance(c, tuple) else (c,)) for path, c in path_constraints.items()}
        path_to_adt = self.path_to_adt(input=True, family=family.SMTFamily(), strip=True)
        for path, constraints in path_constraints.copy().items():
            if path not in path_to_adt:
                raise ValueError(f"{path} is either invalid or not an adt leaf")
            assert path in self.input_varmap
            adt = path_to_adt[path]
            aadt = family.SMTFamily().get_adt_t(adt)
            try:
                constraints = tuple((aadt(c) for c in constraints))
            except Exception as e:
                print("Invalid constraints for {path}")
                raise e
            path_constraints[path] =constraints

        self.path_constraints = path_constraints

    def process_ir_instruction(self, ir_fc):
        return IRMapper(self, ir_fc)


class RewriteRule:
    def __init__(self, ibinding, obinding, ir_fc, arch_fc):
        #Contains all the ir paths that are bound to arch paths
        ir_bounded = set()
        for ir_path, arch_path in ibinding:
            if isinstance(ir_path, tuple):
                ir_bounded.add(ir_path)
            elif not isinstance(ir_path, (BitVector, Bit)):
                raise ValueError(f"{ir_path} is not valid for binding")

        #These are PyFamily bindings
        self.ibinding = ibinding
        self.obinding = obinding
        self.ir_bounded = ir_bounded
        self.ir_fc = ir_fc
        self.arch_fc = arch_fc

    def build_ir_input(self, ir_inputs : tp.Mapping["path", BitVector], family):
        ir_binding = [(val, path) for path, val in ir_inputs.items()]
        ir_input_aadt_t = _input_aadt_t(self.ir_fc, family)
        complete_binding = SimplifyBinding()(ir_input_aadt_t, ir_binding)
        #internally verify entire binding was simplified to a constant
        assert len(complete_binding)==1
        assert complete_binding[0][1] is ()
        input_val = complete_binding[0][0]

        #create dict of input values
        return aadt_product_to_dict(input_val)

    def build_arch_input(self, ir_inputs : tp.Mapping["path", BitVector], family):
        arch_bindings = {}
        complete_binding = []
        ibinding = rebind_binding(self.ibinding, family)
        for ir_path, arch_path in ibinding:
            if isinstance(ir_path, tuple):
                if ir_path not in ir_inputs:
                    raise ValueError(f"{ir_path} must be in ir_inputs")
                complete_binding.append((ir_inputs[ir_path], arch_path))
            else:
                complete_binding.append((ir_path, arch_path))
        arch_input_aadt_t = _input_aadt_t(self.arch_fc, family)
        complete_binding = SimplifyBinding()(arch_input_aadt_t, complete_binding)
        #internally verify entire binding was simplified to a constant
        assert len(complete_binding)==1
        assert complete_binding[0][1] is ()
        input_val = complete_binding[0][0]

        #create dict of input values
        return aadt_product_to_dict(input_val)

    def parse_ir_output(self, outputs):
        output_t = self.ir_fc(family.SMTFamily()).output_t
        output_aadt = family.SMTFamily().get_adt_t(output_t)
        output_value = wrap_outputs(outputs, output_aadt)
        _, values = SMTForms()(output_aadt, value=output_value)
        return values

    def parse_arch_output(self, outputs):
        output_t = self.arch_fc(family.SMTFamily()).output_t
        output_aadt = family.SMTFamily().get_adt_t(output_t)
        output_value = wrap_outputs(outputs, output_aadt)
        _, values = SMTForms()(output_aadt, value=output_value)
        return values

    # Returns a counterexample if found, otherwise None
    def verify(self, solver_name: str = "z3") -> tp.Union[None, "CounterExample"]:
        # create free variable for each ir_val
        ir_path_types = _create_path_to_adt(strip_modifiers(self.ir_fc(family.SMTFamily()).input_t))
        ir_vars = {path:_free_var_from_t(ir_path_types[path]) for path in self.ir_bounded}
        ir_inputs = self.build_ir_input(ir_vars, family.SMTFamily())
        arch_inputs = self.build_arch_input(ir_vars, family.SMTFamily())
        ir = self.ir_fc(family.SMTFamily())()
        arch = self.arch_fc(family.SMTFamily())()
        ir_out_values = self.parse_ir_output(ir(**ir_inputs))
        arch_out_values = self.parse_arch_output(arch(**arch_inputs))

        outputs = []
        for ir_path, arch_path in self.obinding:
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
                return {path: solved_to_bv(var, solver) for path, var in ir_vars.items()}

def _free_var_from_t(T):
    if issubclass(T, SBV):
        return T()
    aadt_t = family.SMTFamily().get_adt_t(T)
    adt_t, assembler_t, bv_t = aadt_t.fields
    assembler = assembler_t(adt_t)
    return bv_t[assembler.width]()

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
        arch_input_path_to_adt = archmapper.path_to_adt(input=True, family=family.SMTFamily())

        #Removes any invalid bindings
        def constraint_filter(binding):
            for ir_path, arch_path in binding:
                if arch_path in archmapper.path_constraints and ir_path is not Unbound:
                    return False
            return True

        ir_path_to_adt = self.path_to_adt(input=True, family=family.SMTFamily())
        #Verify all paths are the same
        assert set(ir_path_to_adt.keys()) == set(self.input_varmap.keys())
        for af in archmapper.input_forms:
            #Verify all paths of form is subset of all paths
            assert set(arch_input_path_to_adt.keys()).issuperset(set(af.varmap.keys()))
            form_arch_input_path_to_adt = {p:T for p, T in arch_input_path_to_adt.items() if p in af.varmap}
            bindings = create_bindings(form_arch_input_path_to_adt, ir_path_to_adt)
            bindings = list(filter(constraint_filter, bindings))
            input_bindings.append(bindings)
        # Check Early out
        self.has_bindings = max(len(bs) for bs in input_bindings) > 0
        if not self.has_bindings:
            return

        # Create output bindings
        arch_output_path_to_adt = archmapper.path_to_adt(input=False, family=family.SMTFamily())
        ir_path_to_adt = self.path_to_adt(input=False, family=family.SMTFamily())

        #binding = [bidx]
        output_bindings = create_bindings(arch_output_path_to_adt, ir_path_to_adt)

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


        self.ib_var = ib_var
        self.ob_var = ob_var
        self.input_bindings = input_bindings
        self.output_bindings = output_bindings
        self.formula = smt.ForAll(list(forall_vars), formula.value)
        self.forall_vars = forall_vars
        self.formula_wo_forall = formula.value

    def solve_efsmt(self, solver_name : str = 'cvc4', itr_limit = 10):
        return efsmt(self.forall_vars, self.formula_wo_forall, BV, itr_limit, solver_name, self)

    def solve(self,
        solver_name : str = 'z3',
        custom_enumeration : tp.Mapping[type, tp.Callable] = {}
    ) -> tp.Union[None, RewriteRule]:
        if not self.has_bindings:
            return None

        with smt.Solver(solver_name, logic=BV) as solver:
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
        if ir_path is Unbound:
            var = am.input_varmap[arch_path]
            bv_val = solved_to_bv(var, solver)
            ir_path = bv_val
        bv_ibinding.append((ir_path, arch_path))

    bv_ibinding = rebind_binding(bv_ibinding, family.PyFamily())
    arch_input_aadt_t = _input_aadt_t(am.peak_fc, family.PyFamily())

    bv_ibinding = SimplifyBinding()(arch_input_aadt_t, bv_ibinding)
    bv_ibinding = _strip_aadt(bv_ibinding)
    return RewriteRule(bv_ibinding, obinding, im.peak_fc, am.peak_fc)

def efsmt(y, phi, logic = BV, maxloops = 10, solver_name = "cvc4", irmapper = None):

    y = set (y)
    x = phi . get_free_variables () - y

    with smt.Solver (logic = logic, name = solver_name) as solver:
        solver.add_assertion(smt.Bool(True))
        loops = 0

        while maxloops is None or loops <= maxloops:
            loops += 1

            eres = solver.solve()

            if not eres:
                return None
            else :
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


def _strip_aadt(binding):
    ret_binding = []
    for ir_path, arch_path in binding:
        if isinstance(ir_path, AssembledADT):
            ir_path = ir_path._value_
        ret_binding.append((ir_path, arch_path))
    return ret_binding
