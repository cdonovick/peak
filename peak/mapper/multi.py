import itertools
from functools import reduce
from types import SimpleNamespace
from hwtypes import strip_modifiers
from peak import family as peak_family, family_closure, Peak, Const
from .mapper import aadt_product_to_dict, external_loop_solve
from .index_var import IndexVar, OneHot, Binary
from .mapper import _get_peak_cls, _create_free_var, create_and_set_bb_outputs, wrap_outputs, is_valid, get_bb_inputs
from .utils import _sort_by_t, pretty_print_binding, solved_to_bv, Unbound
from .formula_constructor import And, Or, Implies
import pysmt.shortcuts as smt
from pysmt.logics import BV

def create_bindings(inputs, outputs, use_unbound=True):
    inputs_by_t = _sort_by_t(inputs)
    outputs_by_t = _sort_by_t(outputs)
    #check early out
    if (not use_unbound) and (not all((o_t in inputs_by_t) for o_t in outputs_by_t)):
        raise ValueError("No matching Bindings")

    #inputs = ir, outputs = arch

    possible_matching = []
    for o_path, o_T in outputs.items():
        poss = []
        if use_unbound:
            poss.append(Unbound)
        if o_T in inputs_by_t:
            poss += inputs_by_t[o_T]
        possible_matching.append(poss)
    assert all(len(p)>0 for p in possible_matching)
    bindings = []
    for l in itertools.product(*possible_matching):
        binding = list(zip(l, outputs.keys()))
        bindings.append(binding)
    return bindings

#This will Solve a multi-rewrite rule N instructions
def Multi(arch_fc, ir_fc, N: int, family=peak_family, IVar: IndexVar = Binary, use_real = True, use_split_instr = False):
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
            stripped_input_t=stripped_input_t,
            input_t = input_t,
            stripped_output_t = stripped_output_t,
            output_t = output_t,
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

    def run_peak(obj, output_aadt, input_dict, bb_prefix):
        bb_outputs = create_and_set_bb_outputs(obj, family=family, prefix=bb_prefix)
        outputs = obj(**input_dict)
        output = wrap_outputs(outputs, output_aadt)
        #output_dict = {(k,): v for k, v in aadt_product_to_dict(output).items()}
        output_dict = aadt_product_to_dict(output)
        bb_inputs = get_bb_inputs(obj)
        return output_dict, bb_inputs, bb_outputs

    ir_inputs = {field: _create_free_var(ir_info.input_aadt[field], f"II_{field}") for field in ir_info.stripped_input_t.field_dict}
    ir_obj = ir_info.cls()
    ir_outputs, ir_bb_inputs, ir_bb_outputs = run_peak(ir_obj, ir_info.output_aadt, ir_inputs, bb_prefix=f"IR_")
    #This contains the 'input binding' for a particular instruction. Indexed by instruction index
    block_info = []

    pysmt_forall_vars = [v.value for v in ir_inputs.values()]
    valid_conds = []


    def translate(path, use_real=True):
        if path[0] == "IR_in":
            assert len(path) == 2
            val = ir_inputs[path[1]]
        elif path[0] == "IR_out":
            assert len(path) == 2
            val = ir_outputs[path[1]]
        elif path[0] == "Arch_in":
            assert len(path) == 3
            val = block_info[path[1]].arch_inputs[path[2]]
        elif path[0] == "Arch_out":
            assert len(path) == 3
            j = path[1]
            assert len(block_info) > j
            if use_real:
                val = block_info[j].real_arch_outputs[path[2]]
            else:
                val = block_info[j].free_arch_outputs[path[2]]
        else:
            assert 0
        return val

    #only output
    def do_bindings(inputs, outputs, name):
        bindings = create_bindings(inputs, outputs, use_unbound=False)
        bind_var = IVar(len(bindings), name=name)
        valid_conds.append(bind_var.is_valid())
        impl_conds = []
        # Will be Ored
        for b, binding in enumerate(bindings):
            b_match = bind_var.match_index(b)

            # TO be anded
            bind_conds = [b_match]
            for ipath, opath in binding:
                ival = translate(ipath, use_real=True)
                oval = translate(opath, use_real=True)
                bind_conds.append(ival == oval)
            impl_conds.append(And(bind_conds))
        return bindings, bind_var, Or(impl_conds)


    for i in range(N):
        arch_obj = arch_info.cls()
        input_aadt = arch_info.input_aadt
        output_aadt = arch_info.output_aadt
        arch_inputs = {field:_create_free_var(input_aadt[field], f"ArchIn_I{i}_{field}") for field in arch_info.stripped_input_t.field_dict}
        free_arch_outputs = {field:_create_free_var(output_aadt[field], f"ArchOut_I{i}_{field}") for field in arch_info.output_t.field_dict}
        real_arch_outputs, bb_inputs, bb_outputs = run_peak(arch_obj, output_aadt, arch_inputs, bb_prefix=f"{i}.BB.{arch_info.cls.__name__}")

        pysmt_forall_vars += [v.value for field, v in arch_inputs.items() if field in arch_info.non_const_dict]
        pysmt_forall_vars += [v.value for v in bb_outputs.values()]


        #Creating i'th binding
        #Consisting of the ir_inputs, arch_inputs, Arch_output[N-1 ... 1])
        inputs = {
            **{("IR_in", field):T for field, T in ir_info.input_t.field_dict.items()},
            #**{(f"Arch_in", i, field):T for field, T in arch_info.non_const_dict.items()},
        }
        for j in range(i):
            inputs = {
                **inputs,
                **{("Arch_out", j, field):T for field, T in arch_info.output_t.field_dict.items()},
            }
        outputs = {(f"Arch_in", i, field):T for field, T in arch_info.non_const_dict.items()}
        bindings = create_bindings(inputs, outputs, use_unbound=True)
        block_info.append(SimpleNamespace(
            arch_inputs=arch_inputs,
            free_arch_outputs=free_arch_outputs,
            real_arch_outputs=real_arch_outputs,
            obj=arch_obj,
            bb_outputs=bb_outputs,
            bb_inputs=bb_inputs,
            bindings=bindings
        ))

    #Out of the cross product of the bindings, filter out everything that does not use all the ir inputs
    ir_paths = [("IR_in", field) for field in ir_info.input_t.field_dict]
    all_bindings = [block.bindings for block in block_info]

    orig_bindings = reduce(lambda x, y: x*y, [len(b) for b in all_bindings])
    def filt(x):
        bind = [b[x[j]] for j, b in enumerate(all_bindings)]
        found = [0 for _ in ir_paths]
        for j, p in enumerate(ir_paths):
            for binding in bind:
                for input, _ in binding:
                    if input == p:
                        found[j] += 1
        return all(f in (1,) for f in found)
    valid_bindings = list(filter(filt, itertools.product(*[range(len(bindings)) for bindings in all_bindings])))
    if len(valid_bindings) == 0:
        raise ValueError("There are no valid Bindings")
    bind_var = IVar(len(valid_bindings), "bind_in")
    valid_conds.append(bind_var.is_valid())

    # Will be Ored
    impl_conds = []
    for b, bind_indices in enumerate(valid_bindings):
        assert len(bind_indices) == N
        b_match = bind_var.match_index(b)

        # TO be anded
        bind_conds = [b_match]
        for bind_index, block in zip(bind_indices, block_info):
            binding = block.bindings[bind_index]
            for ipath, opath in binding:
                if ipath is Unbound:
                    ipath = opath
                ival = translate(ipath, use_real=use_real)
                oval = translate(opath, use_real=use_real)
                bind_conds.append(ival == oval)
        impl_conds.append(And(bind_conds))

    #set fake to real except for the last one
    if not use_real:
        if N==1:
            free_repl = family.SMTFamily().Bit(True)
        else:
            free_repl = []
            for i in range(N-1):
                real = block_info[i].real_arch_outputs
                fake = block_info[i].free_arch_outputs
                for vr, vf in zip(real.values(), fake.values()):
                    pysmt_forall_vars.append(vf.value)
                    free_repl.append(vf==vr)
            free_repl = And(free_repl)



    #Output bindings
    #This assumes that the output bindings will only be a function of the outputs of the last instruction
    #Might not hold true if IR node is computing multiple things (ie i64.Add)
    inputs = {
        **{(f"Arch_out", N-1, field):T for field, T in arch_info.output_t.field_dict.items()},
    }
    outputs = {(f"IR_out", field):T for field, T in ir_info.output_t.field_dict.items()}
    out_bindings, bind_out_var, out_conds = do_bindings(inputs, outputs, f"bind_out")

    block_info.append(SimpleNamespace(
        bindings=out_bindings,
        bind_var=bind_out_var,
        impl_conds=out_conds
    ))


    if use_split_instr:
        #This will use an SMT Form instruction instead of a raw instruction. Might be faster
        raise NotImplementedError()
    else:
        for i in range(N):
            arch_inputs = block_info[i].arch_inputs
            # Make sure instruction is valid
            for field in arch_info.const_dict:
                valid_conds.append(is_valid(arch_inputs[field]))

    valid_cond = And(valid_conds)
    if use_real:
        impl_cond = Or(impl_conds)
    else:
        impl_cond = And([free_repl, Or(impl_conds)])
    F = out_conds
    formula = And([valid_cond, Implies(impl_cond, F)])
    formula = formula.to_hwtypes()
    forall_vars = pysmt_forall_vars
    formula_wo_forall = formula.value
    formula = smt.ForAll(pysmt_forall_vars, formula.value)

    info = SimpleNamespace(
        N=N,
        block_info=block_info,
        arch_info=arch_info,
        bind_var=bind_var,
        valid_bindings=valid_bindings,
    )
    def solve(maxloops=20, logic=BV, solver_name="z3"):
        return external_loop_solve(forall_vars, formula_wo_forall, logic=logic, maxloops=maxloops, solver_name=solver_name, rr_from_solver=RR, irmapper=info)
    return solve

#Definititely a bit hacked. Really should contain a verify function and better pretty printers
def RR(solver, info):
    if solver is None:
        return None

    def get_info():
        N = info.N
        block_info = info.block_info
        arch_info = info.arch_info
        bind_var = info.bind_var
        bind_val = bind_var.decode(int(solved_to_bv(bind_var.var, solver)))
        print(bind_var.var.value, bind_val)
        binding_indices = info.valid_bindings[bind_val]
        for i in range(N):
            print("*"*100)
            print(f"Instruction {i}")
            binding = block_info[i].bindings[binding_indices[i]]
            pretty_print_binding(binding)
            instrs = [block_info[i].arch_inputs[field] for field in arch_info.const_dict]
            ivals = [solved_to_bv(instr._value_,solver) for instr in instrs]
            print(ivals)
        return info
    return get_info
