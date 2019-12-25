from hwtypes import Product, Sum, Enum, Tuple
from hwtypes import SMTBitVector, SMTBit
from peak.assembler import Assembler
from peak.assembler import AssembledADT
from peak.mapper.utils import Tag, Match, generic_aadt_smt
from examples.min_pe.sim import gen_sim
from examples.min_pe.sim import gen_isa
from functools import reduce
import pysmt.shortcuts as smt
from pysmt.logics import BV
import typing as tp
import math
import operator
from functools import partial

SBV = SMTBitVector

def add(a, b):  return a + b
def sub(a, b):  return b - a
def and_(a, b): return a & b
def nand(a, b): return ~(a & b)
def or_(a, b):  return a | b
def nor(a, b):  return ~(b | a)
def mul(a, b):  return a * b
def shftr(a, b): return a >> b
def shftl(a, b): return a << b
targets = (
    add,
    sub,
    and_,
    nand,
    or_,
    nor,
    mul,
    shftr,
    shftl,
)
Word, Bit, Inst, sim = gen_sim(SBV.get_family())

T = Tuple[Word, Bit]
S = Sum[Word, T]

Inst_aadt = AssembledADT[Inst, Assembler, SBV]



#Forms:

class Unbound: pass


def log2(x):
    #verify it is a power of 2
    assert x & (x-1) == 0
    return x.bit_length() - 1

#TODO maybe helper function for creating predicate and value
#Manually creating all the forms
forms = [
    {("operand_1",):Word},
    {("operand_1",):T}
]


#Manually create all the bindings
form_bindings = [[], []]

#form 0 (operand_1, Word)
#[a -> operand_0, b -> (operand_1, Word)]
#[b -> operand_0, a -> (operand_1, Word)]

form_bindings[0].append([
    (("a",), ("operand_0",)),
    (("b",), ("operand_1", Word)),
    (Unbound, ("Opcode",))
])
form_bindings[0].append([
    (("b",), ("operand_0",)),
    (("a",), ("operand_1", Word)),
    (Unbound, ("Opcode",))
])

#form 1: (operand_1, Tuple[Word, Bit])
#[a -> operand_0, b -> (operand_1, Tuple, 0)]
#[b -> operand_0, a -> (operand_1, Tuple, 0)]
form_bindings[1].append([
    (("a",), ("operand_0",)),
    (("b",), ("operand_1", T, 0)),
    (Unbound, ("operand_1", T, 1)),
    (Unbound, ("Opcode",))
])
form_bindings[1].append([
    (("b",), ("operand_0",)),
    (("a",), ("operand_1", T, 0)),
    (Unbound, ("operand_1", T, 1)),
    (Unbound, ("Opcode",))
])
def test_min_pe_mapping():


    arch_forms, arch_varmap = generic_aadt_smt(Inst_aadt)

    for form in arch_forms:
        print(form.path_dict)
        assert form.path_dict in forms

    if arch_forms[0].path_dict != forms[0]:
        print("RRRRRRRRRRRRRR")
        #swap the forms and bindings
        arch_forms = list(reversed(arch_forms))
    else:
        print("TTTTTTTTTTTTTTT")
    for form in forms:
        print(form)
    #Check that manually created forms and bindings are consistent
    for form in forms:
        for path, choice in form.items():
            match_path = path + (Match,)
            assert match_path in arch_varmap
            assert choice in arch_varmap[match_path]
    for bindings in form_bindings:
        for binding in bindings:
            print(binding)
            for ir_path, arch_path in binding:
                assert arch_path in arch_varmap

    #Automatically create the form/binding precondition
    num_forms = len(forms)
    max_bindings = max(len(b) for b in form_bindings)

    form_SBV = SBV[num_forms]
    binding_SBV = SBV[max_bindings]

    form_var = form_SBV()
    binding_var = binding_SBV()

    or_reduce = partial(operator.or_, reduce)

    for target in targets:
        #Manually create ir_varmap (This will be done automatically in the future)
        print("Trying", target.__name__)
        ir_varmap = {
            ("a",): SBV[8](),
            ("b",): SBV[8]()
        }
        ir_out = target(ir_varmap[("a",)], ir_varmap[("b",)])

        #Build precondition.
        precondition = SMTBit(0)
        for fi, form in enumerate(arch_forms):
            #form_condition represnts the & of all the appropriate matches
            form_condition = SMTBit(1)
            for path, choice in form.path_dict.items():
                match_path = path + (Match,)
                form_condition &= arch_varmap[match_path][choice]
            precondition = (form_var == 2**fi).ite(form_condition, precondition)

        #Build the constraint
        general_arch_out = sim(arch_forms[0].value)
        arch_out0 = SBV[general_arch_out.size](0)
        arch_out = arch_out0
        for fi, bindings in enumerate(form_bindings):
            general_arch_out = sim(arch_forms[fi].value)

            form_arch_out = arch_out0
            for bi, binding in enumerate(bindings):
                #Build substitution map
                submap = []
                for ir_path, arch_path in binding:
                    if ir_path is Unbound:
                        continue
                    ir_var = ir_varmap[ir_path]
                    arch_var = arch_varmap[arch_path]
                    submap.append((arch_var, ir_var))
                binding_arch_out = general_arch_out.substitute(*submap)
                form_arch_out = (binding_var==(2**bi)).ite(binding_arch_out, form_arch_out)
            arch_out = (form_var==(2**fi)).ite(form_arch_out, arch_out)
        forall_vars = [var.value for var in ir_varmap.values()]

        with smt.Solver('cvc4', logic=BV) as solver:
            solver.add_assertion(precondition.value)
            constraint = smt.ForAll(forall_vars, (ir_out == arch_out).value)
            solver.add_assertion(constraint)
            print("Solving", target)
            if not solver.solve():
                assert target in (mul, shftr, shftl)
                print("Successfully did not find", target)
                continue
            assert target in (add, sub, and_, nand, or_, nor)
            print("Successfully found", target)
            form_val = solver.get_value(form_var.value).constant_value()
            binding_val = solver.get_value(binding_var.value).constant_value()
            form_val = log2(form_val)
            binding_val = log2(binding_val)
            print("for target", target.__name__)
            print("form", form_val)
            print("binding", binding_val)
            binding = form_bindings[form_val][binding_val]
            arch_vals = {}
            for ir_path, arch_path in binding:
                if ir_path is Unbound:
                    var = arch_varmap[arch_path]
                    var_val = solver.get_value(var.value).constant_value()
                    print(var_val, arch_path)
                else:
                    print(ir_path, arch_path)

