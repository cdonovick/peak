from hwtypes import Product, Sum, Enum, Tuple
from hwtypes import SMTBitVector, SMTBit
from peak.assembler import Assembler
from peak.assembler import AssembledADT
from peak.mapper.utils import Unbound, Match, SMTForms, extract, aadt_product_to_dict
from examples.min_pe.sim import gen_sim
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
Word, Bit, Inst, PE = gen_sim(SBV.get_family())

T = Tuple[Word, Bit]
S = Sum[Word, T]


def log2(x):
    #verify it is a power of 2
    assert x & (x-1) == 0
    return x.bit_length() - 1

#Manually creating all the forms
forms = [
    {("inst","operand_1",):Word},
    {("inst","operand_1",):T}
]


#Manually create all the bindings
form_bindings = [[], []]

#form 0 (operand_1, Word)
#[a -> operand_0, b -> (operand_1, Word)]
#[b -> operand_0, a -> (operand_1, Word)]

form_bindings[0].append([
    (("a",), ("inst","operand_0",)),
    (("b",), ("inst","operand_1", Word)),
    (Unbound, ("inst","Opcode",))
])
form_bindings[0].append([
    (("b",), ("inst","operand_0",)),
    (("a",), ("inst","operand_1", Word)),
    (Unbound, ("inst","Opcode",))
])

#form 1: (operand_1, Tuple[Word, Bit])
#[a -> operand_0, b -> (operand_1, Tuple, 0)]
#[b -> operand_0, a -> (operand_1, Tuple, 0)]
form_bindings[1].append([
    (("a",), ("inst","operand_0",)),
    (("b",), ("inst","operand_1", T, 0)),
    (Unbound, ("inst","operand_1", T, 1)),
    (Unbound, ("inst","Opcode",))
])
form_bindings[1].append([
    (("b",), ("inst","operand_0",)),
    (("a",), ("inst","operand_1", T, 0)),
    (Unbound,("inst","operand_1", T, 1)),
    (Unbound,("inst","Opcode",))
])
def test_min_pe_mapping():

    pe = PE()
    input_aadt_t = AssembledADT[PE.get_inputs(), Assembler, SBV]
    arch_forms, arch_varmap = SMTForms()(input_aadt_t)

    for form in arch_forms:
        assert form.path_dict in forms

    if arch_forms[0].path_dict != forms[0]:
        #swap the forms and bindings
        arch_forms = list(reversed(arch_forms))

    #Check that manually created forms and bindings are consistent
    for form in forms:
        for path, choice in form.items():
            match_path = path + (Match,)
            assert match_path in arch_varmap
            assert choice in arch_varmap[match_path]
    for bindings in form_bindings:
        for binding in bindings:
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
        output_aadt_t = AssembledADT[PE.get_outputs(), Assembler, SBV]
        out_width = output_aadt_t.assembler_t(output_aadt_t.adt_t).width
        arch_out0 = SBV[out_width](0)
        arch_out = arch_out0
        for fi, bindings in enumerate(form_bindings):
            inputs = aadt_product_to_dict(arch_forms[fi].value)
            general_arch_out = pe(**inputs)

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

        with smt.Solver('z3', logic=BV) as solver:
            solver.add_assertion(precondition.value)
            constraint = smt.ForAll(forall_vars, (ir_out == arch_out).value)
            solver.add_assertion(constraint)
            print("Solving", target)
            if not solver.solve():
                assert target in (mul, shftr, shftl)
                print("Successfully did not find", target)
                continue
            assert target in (add, sub, and_, nand, or_, nor)

            ##Test that the values found are valid
            arch_fc = lambda f: gen_sim(f)[3]
            bounds, binding = extract(solver, Assembler, form_var, binding_var, form_bindings, arch_varmap, arch_fc)
            assert ("a",) in bounds
            assert ("b",) in bounds
            assert 0
            for a,b in ((Word.random(Word.size),Word.random(Word.size)) for _ in range(16)):
                gold = target(a=a,b=b)
                pe_inputs = input_builder(arch_fc, binding, {("a",):a,("b",):b})
                res = pe_BV(**pe_inputs)
                assert gold == res


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

