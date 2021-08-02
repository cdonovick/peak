import itertools
from functools import reduce
from types import SimpleNamespace
from hwtypes import strip_modifiers
from peak import family as peak_family, family_closure, Peak, Const
from .mapper import aadt_product_to_dict
from .index_var import IndexVar, OneHot, Binary
from .mapper import _get_peak_cls, _create_free_var, create_and_set_bb_outputs, wrap_outputs, is_valid, get_bb_inputs
from .utils import _sort_by_t, pretty_print_binding, solved_to_bv
from .formula_constructor import And, Or, Implies
import pysmt.shortcuts as smt
from pysmt.logics import BV

#This will Solve a multi-rewrite rule N instructions
def create_bindings(inputs, outputs):
#def create_bindings(needed_inputs, aux_inputs, outputs):
    #assert needed_inputs.keys() & aux_inputs.keys() == set()
    #inputs = {**needed_inputs, **aux_inputs}
    inputs_by_t = _sort_by_t(inputs)
    outputs_by_t = _sort_by_t(outputs)
    #check early out
    if not all((o_t in inputs_by_t) for o_t in outputs_by_t):
        raise ValueError("No matching Bindings")

    #inputs = ir, outputs = arch
    possible_matching = {o_path:inputs_by_t[o_T] for o_path, o_T in outputs.items()}
    bindings = []
    for l in itertools.product(*possible_matching.values()):
        binding = list(zip(l, outputs.keys()))
        bindings.append(binding)
    return bindings

def Multi(arch_fc, ir_fc, N: int, family=peak_family, IVar: IndexVar = Binary, max_loops=50):
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


    def translate(path):
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
            val = block_info[j].real_arch_outputs[path[2]]
        else:
            assert 0
        return val
    def do_bindings(inputs, outputs, name):
        bindings = create_bindings(inputs, outputs)
        bind_var = IVar(len(bindings), name=name)
        valid_conds.append(bind_var.is_valid())
        print(bind_var.var, len(bindings))
        impl_conds = []
        # Will be Ored
        for b, binding in enumerate(bindings):
            b_match = bind_var.match_index(b)

            # TO be anded
            bind_conds = [b_match]
            for ipath, opath in binding:
                ival = translate(ipath)
                oval = translate(opath)
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

        #Make sure instruction is valid
        for field in arch_info.const_dict:
            valid_conds.append(is_valid(arch_inputs[field]))

        block_info.append(SimpleNamespace(
            arch_inputs=arch_inputs,
            free_arch_outputs=free_arch_outputs,
            real_arch_outputs=real_arch_outputs,
            obj=arch_obj,
            bb_outputs=bb_outputs,
            bb_inputs=bb_inputs,
        ))

        #Creating i'th binding
        #Consisting of the ir_inputs, arch_inputs, Arch_output[N-1 ... 1])
        inputs = {
            **{("IR_in", field):T for field, T in ir_info.input_t.field_dict.items()},
            **{(f"Arch_in", i, field):T for field, T in arch_info.non_const_dict.items()},
        }
        for j in range(i):
            inputs = {
                **inputs,
                **{("Arch_out", j, field):T for field, T in arch_info.output_t.field_dict.items()},
            }
        outputs = {(f"Arch_in", i, field):T for field, T in arch_info.non_const_dict.items()}
        bindings, bind_var, impl_conds = do_bindings(inputs, outputs, f"bind{i}")
        #Hack
        block_info[-1].bindings = bindings
        block_info[-1].bind_var = bind_var
        block_info[-1].impl_conds = impl_conds

    ir_paths = [("IR_in", field) for field in ir_info.input_t.field_dict]
    b_map = [block.bindings for block in block_info]
    b_len = [len(b) for b in b_map]
    print(b_len)
    tot = reduce(lambda x,y: x*y, b_len, 1)
    print("TOT", tot)

    def filt(x):
        bind = [b[x[j]] for j, b in enumerate(b_map)]
        found = [0 for _ in ir_paths]
        for j, p in enumerate(ir_paths):
            for binding in bind:
                for input, _ in binding:
                    if input == p:
                        found[j] += 1
        return all(f==1 for f in found)
    b_prod = list(filter(filt, itertools.product(*[range(l) for l in b_len])))
    print(len(b_prod))
    #for j, bs in enumerate(b_prod):
    #    print(f"Binding(s) {j}", "{")
    #    for k, b in enumerate(bs):
    #        print(k)
    #        pretty_print_binding(b_map[k][b])
    #    print("}")
    assert 0




    #Output bindings
    #This assumes that the output bindings will only be a function of the outputs of the last instruction
    #Might not hold true if IR node is computing multiple things.
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
    valid_cond = And(valid_conds)
    impl_cond = And([b.impl_conds for b in block_info[:-1]])
    F = out_conds
    formula = And([valid_cond, Implies(impl_cond, F)])
    print(formula.serialize(), flush=True)
    formula = formula.to_hwtypes()
    print("FA", pysmt_forall_vars, flush=True)
    forall_vars = pysmt_forall_vars
    formula_wo_forall = formula.value
    formula = smt.ForAll(pysmt_forall_vars, formula.value)

    info = SimpleNamespace(
        N=N,
        block_info=block_info,
        arch_info=arch_info
    )
    return external_loop_solve(forall_vars, formula_wo_forall, info, logic=BV, maxloops=max_loops, solver_name="z3")

def RR(info, solver):
    if solver is None:
        return None
    N = info.N
    block_info = info.block_info
    arch_info = info.arch_info
    for i in range(N+1):
        print("*"*100)
        print(f"Instruction {i}")
        bindings = block_info[i].bindings
        bind_var = block_info[i].bind_var
        bind_val = bind_var.decode(int(solved_to_bv(bind_var.var, solver)))
        binding = bindings[bind_val]
        print(bind_var.var.value)
        pretty_print_binding(binding)
        if i !=N:
            instrs = [block_info[i].arch_inputs[field] for field in arch_info.const_dict]
            ivals = [solved_to_bv(instr._value_,solver) for instr in instrs]
            print(ivals)
    return info

def external_loop_solve(y, phi, rr_info, logic = BV, maxloops=10, solver_name = "cvc4"):

    y = set(y) #forall_vars
    x = phi.get_free_variables() - y #exist vars

    with smt.Solver(logic=logic, name=solver_name) as solver:
        solver.add_assertion(smt.Bool(True))
        loops = 0
        #print("Solving")
        while maxloops is None or loops <= maxloops:
            if loops %10==0:
                print(f"{loops}.", end="", flush=True)
            loops += 1
            eres = solver.solve()

            if not eres:
                return None
            else:
                tau = {v: solver.get_value(v) for v in x}
                sub_phi = phi.substitute(tau).simplify()
                model = smt.get_model(smt.Not(sub_phi), solver_name=solver_name, logic=logic)

                if model is None:
                    return RR(rr_info, solver)
                else :
                    sigma = {v: model.get_value(v) for v in y}
                    sub_phi = phi.substitute(sigma).simplify()
                    solver.add_assertion(sub_phi)
        raise ValueError(f"Unknown result in efsmt in {maxloops} number of iterations")

