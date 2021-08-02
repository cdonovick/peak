import itertools
from collections import OrderedDict
from types import SimpleNamespace

from hwtypes import strip_modifiers

from peak import family as peak_family, family_closure, Peak, Const
from . import aadt_product_to_dict
from .index_var import IndexVar, OneHot, Binary

#This will Solve a multi-rewrite rule N instructions
from .mapper import _get_peak_cls, _create_free_var, create_and_set_bb_outputs, wrap_outputs
from .utils import _sort_by_t, pretty_print_binding


def create_bindings(inputs, outputs):
#def create_bindings(needed_inputs, aux_inputs, outputs):
    #assert needed_inputs.keys() & aux_inputs.keys() == set()
    #inputs = {**needed_inputs, **aux_inputs}
    assert set(outputs.keys()).issubset(set(inputs.keys()))
    inputs_by_t = _sort_by_t(inputs)
    outputs_by_t = _sort_by_t(outputs)

    #check early out
    if not all((o_t in inputs_by_t) for o_t in outputs_by_t):
        return []

    #inputs = ir, outputs = arch
    possible_matching = {o_path:inputs_by_t[o_T] for o_path, o_T in outputs.items()}
    bindings = []
    for l in itertools.product(*possible_matching.values()):
        binding = list(zip(l, outputs.keys()))
        bindings.append(binding)
    return bindings

class Multi:
    def __init__(self, arch_fc, ir_fc, N: int, family=peak_family, IVar: IndexVar = Binary):
        self.family = family

        #Does things
        def parse_peak_fc(peak_fc):
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
            const_dict = {field: T for field, T in input_t.field_dict.items() if issubclass(T, Const)}
            non_const_dict = {field: T for field, T in input_t.field_dict.items() if not issubclass(T, Const)}
            return SimpleNamespace(
                input_aadt=input_aadt_t,
                input_t = stripped_input_t,
                output_t = stripped_output_t,
                output_aadt=output_aadt_t,
                cls=Peak_cls,
                const_dict=const_dict,
                non_const_dict=non_const_dict,
            )

        ir_info = parse_peak_fc(ir_fc)
        arch_info = parse_peak_fc(arch_fc)
        if len(ir_info.const_dict) != 0:
            raise NotImplementedError()
        if len(arch_info.const_dict) != 1:
            raise NotImplementedError()

        for i in range(N):
            arch_obj = arch_info.cls()
            input_aadt = arch_info.input_aadt
            output_aadt = arch_info.output_aadt
            free_arch_inputs = {field:_create_free_var(input_aadt[field], f"AI{i}_{field}") for field in arch_info.input_t.field_dict}
            free_arch_outputs = {field:_create_free_var(output_aadt[field], f"AO{i}_{field}") for field in arch_info.output_t.field_dict}
            bb_output_dict = create_and_set_bb_outputs(arch_obj, family=family, prefix=f"{i}.BB.{arch_info.cls.__name__}")
            outputs = arch_obj(**free_arch_inputs)
            output = wrap_outputs(outputs, output_aadt)
            real_arch_outputs = {(k,): v for k, v in aadt_product_to_dict(output).items()}

            #Creating i'th binding
            #Consisting of the ir_inputs, arch_inputs, Arch[N-1 ... 1])_outputs
            inputs = {
                **{("IR", field):T for field, T in ir_info.input_t.field_dict.items()},
                **{(f"Ain", i, field):T for field, T in arch_info.non_const_dict.items()},
            }
            for j in range(i):
                inputs = {
                    **inputs,
                    **{("Aout", j, field):T for field, T in arch_info.output_t.field_dict.items()},
                }
            outputs = {(f"Ain", i, field):T for field, T in arch_info.non_const_dict.items()}
            bindings = create_bindings(inputs, outputs)
            bind_var = IVar(len(bindings))
            for b, binding in enumerate(bindings):
                b_match = bind_var.match_index(b)
            for bi, ibinding in enumerate(ibindings):
                conditions = fi_conditions + [ib_var.match_index(bi)]
                fb = (fi, bi)
                for ir_path, arch_path in ibinding:
                    arch_name = ".".join(["A"] + [str(p) for p in arch_path])
                    arch_var = archmapper.input_varmap[arch_path]
                    name_to_var[arch_name] = arch_var
                    is_unbound = ir_path is Unbound
                    is_constrained = arch_path in self.archmapper.path_constraints
                    is_const = issubclass(arch_input_path_to_adt[arch_path], Const)
                    if is_constrained:
                        if not is_unbound:
                            raise NotImplementedError()
                    if is_unbound and not is_const:
                        forall_to_fbs[arch_name].append(fb)
                    elif is_unbound and is_const:
                        exists_to_fbs[arch_name].append(fb)
                    elif not is_unbound:
                        assert not is_unbound
                        ir_name = ".".join(["I"] + [str(p) for p in ir_path])
                        ir_var = self.input_varmap[ir_path]
                        name_to_var[ir_name] = ir_var
                        forall_to_fbs[arch_name].append(fb)
                        forall_to_fbs[ir_name].append(fb)
                        conditions.append(arch_var == ir_var)
                fb_conditions[(fi, bi)] = conditions








        #exists(instr0,instrN, bind_var0..bind_varN, output_bind)
        #()
