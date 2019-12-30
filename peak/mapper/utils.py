from peak.assembler import Assembler
from peak.assembler import AssembledADT
from peak.assembler import AssembledADTRecursor
import typing as tp
from hwtypes import BitVector, Bit, SMTBitVector, SMTBit
from hwtypes import Product, Sum, Tuple, Enum
from hwtypes import AbstractBit, AbstractBitVector
from collections import namedtuple, OrderedDict
import itertools as it
from functools import wraps
import inspect
from hwtypes.modifiers import is_modified, get_modifier, get_unmodified
from hwtypes.adt_util import rebind_bitvector

class Tag: pass
class Match: pass
class Unbound: pass

Form = namedtuple("Form", ["value","path_dict"])

#Constructs a free variable for each leaf node and each 
# sum tag. This is returned via varmap which is a mapping
# from adt tree paths to free variables. Also included in
# the varmap is the match expressions and tags for each sum.
#For each form, it will return a single SMT expression representing that form
class SMTForms(AssembledADTRecursor):
    def __call__(self, aadt_t, path=()) -> (tp.List[Form], tp.Mapping["path",SMTBitVector]):
        return super().__call__(aadt_t, path)

    def bv(self, aadt_t, path):
        #Leaf node
        bv_var = aadt_t()
        varmap = {path: bv_var}
        return [Form(value=bv_var,path_dict={})], varmap

    def enum(self, aadt_t, path):
        #Leaf node
        adt_t, assembler_t, bv_t = aadt_t.fields
        assembler = assembler_t(adt_t)
        bv = bv_t[assembler.width]()
        aadt_value = aadt_t(bv)
        varmap = {path: bv}
        return [Form(value=aadt_value,path_dict={})], varmap

    def sum(self, aadt_t, path):
        adt_t, assembler_t, bv_t = aadt_t.fields
        assembler = assembler_t(adt_t)
        #Create Tag
        tag = SMTBitVector[assembler.tag_width]()

        forms = []
        varmap = {}
        varmap[path + (Tag,)] = tag
        varmap[path + (Match,)] = {}
        for field in adt_t.fields:
            field_tag_value = assembler.assemble_tag(field, bv_t)
            tag_match = (tag==field_tag_value)
            varmap[path + (Match,)][field] = tag_match
            sub_aadt_t = aadt_t[field]
            sub_forms, sub_varmap = self(sub_aadt_t, path + (field,))
            #update sub_forms with current match path
            for sub_form in sub_forms:
                assert path not in sub_form.path_dict
                path_dict = {path:field,**sub_form.path_dict}
                value = aadt_t.from_fields(field,sub_form.value,tag_bv=tag)
                forms.append(Form(value=value,path_dict=path_dict))
            varmap.update(sub_varmap)
        return forms, varmap

    def product(self, aadt_t, path):
        adt_t, assembler_t, bv_t = aadt_t.fields
        forms = []
        varmap = {}

        forms_to_product = []
        #Needed to guarentee order is consistent
        adt_items =  list(adt_t.field_dict.items())
        for field_name, field in adt_items:
            sub_aadt_t = aadt_t[field_name]
            sub_forms, sub_varmap = self(sub_aadt_t, path + (field_name,))
            varmap.update(sub_varmap)
            forms_to_product.append(sub_forms)
        for sub_forms in it.product(*forms_to_product):
            value_dict = {}
            path_dict = {}
            for i,sub_form in enumerate(sub_forms):
                field_name = adt_items[i][0]
                value_dict[field_name] = sub_form.value
                path_dict.update(sub_form.path_dict)
            value = aadt_t.from_fields(**value_dict)
            forms.append(Form(value=value,path_dict=path_dict))
        return forms, varmap

    def tuple(self, aadt_t, path):
        adt_t, assembler_t, bv_t = aadt_t.fields
        forms = []
        varmap = {}

        forms_to_product = []
        for _idx, (idx, field) in enumerate(adt_t.field_dict.items()):
            assert _idx == idx
            sub_aadt_t = aadt_t[idx]
            sub_forms, sub_varmap = self(sub_aadt_t, path + (idx,))
            varmap.update(sub_varmap)
            forms_to_product.append(sub_forms)
        for sub_forms in it.product(*forms_to_product):
            values = []
            path_dict = {}
            for sub_form in sub_forms:
                values.append(sub_form.value)
                path_dict.update(sub_form.path_dict)
            value = aadt_t.from_fields(*values)
            forms.append(Form(value=value,path_dict=path_dict))
        return forms, varmap

def check_leaf(required=False):
    def dec(f):
        @wraps(f)
        def method(self, aadt_t, binding):
            if required:
                assert len(binding) == 1
                assert binding[0][1] is ()
            if len(binding)==1 and binding[0][1] is ():
                return binding
            return f(self,aadt_t,binding)
        return method
    return dec

#This will combine as many paths as possible together
class SimplifyBinding(AssembledADTRecursor):
    def __call__(self, aadt_t, binding : tp.List[tp.Tuple['ir_path','arch_path']]):
        return super().__call__(aadt_t, binding)

    @check_leaf(required=True)
    def bv(self, aadt_t, binding):
        assert 0
        pass

    @check_leaf(required=True)
    def enum(self, aadt_t, binding):
        assert 0
        pass

    @check_leaf(required=False)
    def sum(self, aadt_t, binding):
        adt_t, assembler_t, bv_t = aadt_t.fields
        #Find the correct field
        sub_field = binding[0][1][0]
        sub_binding = []
        for ir_path, arch_path in binding:
            assert arch_path[0] == sub_field
            sub_binding.append((ir_path,arch_path[1:]))
        sub_aadt_t = aadt_t[sub_field]

        simplified_binding = self(sub_aadt_t,sub_binding)

        #Completely simplified if onlying one binding and ir_path is a value instead of a path
        if len(simplified_binding)==1 and not isinstance(simplified_binding[0][0],tuple):
            sub_value, arch_path = simplified_binding[0]
            assert arch_path is ()
            value = aadt_t.from_fields(sub_field,sub_value)
            return [(value,())]
        else:
            return [(ir_path, (sub_field,) + arch_path) for ir_path, arch_path in simplified_binding]

    def product_or_tuple(self, aadt_t, binding, *, is_product):
        adt_t, assembler_t, bv_t = aadt_t.fields
        sub_binding_dict = {}
        for ir_path, arch_path in binding:
            field_name = arch_path[0]
            assert field_name in adt_t.field_dict
            sub_binding_dict.setdefault(field_name,[])
            sub_binding_dict[field_name].append((ir_path, arch_path[1:]))
        assert len(sub_binding_dict) == len(adt_t.field_dict)

        simplify = True
        simplified_binding_dict = {}
        for field_name, sub_binding in sub_binding_dict.items():
            simplified_binding = self(aadt_t[field_name],sub_binding)
            simplified_binding_dict[field_name] = simplified_binding
            simplify &= len(simplified_binding)==1 and not isinstance(simplified_binding[0][0],tuple)

        if simplify:
            value_dict = {field_name:b[0][0] for field_name, b in simplified_binding_dict.items()}
            if is_product:
                value = aadt_t.from_fields(**value_dict)
            else: #is tuple
                values = [v for _,v in sorted(value_dict.items())]
                value = aadt_t.from_fields(*values)
            return [(value,())]
        else:
            ret_binding = []
            for sub_field, binding in simplified_binding_dict.items():
                ret_binding += [(ir_path, (sub_field,) + arch_path) for ir_path, arch_path in binding]
            return ret_binding

    @check_leaf(required=False)
    def product(self, aadt_t, binding):
        return self.product_or_tuple(aadt_t, binding, is_product=True)

    @check_leaf(required=False)
    def tuple(self, aadt_t, binding):
        return self.product_or_tuple(aadt_t, binding, is_product=False)


def log2(x):
    #verify it is a power of 2
    assert x & (x-1) == 0
    return x.bit_length() - 1

def solved_to_bv(var, solver):
    solver_value = solver.get_value(var.value).constant_value()
    if isinstance(var,SMTBit):
        return Bit(solver_value)
    else:
        return BitVector[var.size](solver_value)

#returns a binding where all aadt values are changed to binding
def smt_binding_to_bv_binding(binding):
    #TODO arch_path types need to be changed to product
    ret_binding = []
    for ir_path, arch_path in binding:
        arch_path = tuple(rebind_type(t,Bit.get_family()) for t in arch_path)
        ret_binding.append((ir_path, arch_path))
    return ret_binding

#returns simplified binding with bitvectors
def extract(solver, Assembler, form_var, binding_var, form_bindings, arch_varmap, arch_fc):
    arch = arch_fc(Bit.get_family())
    input_t = arch.get_inputs()
    aadt_t = AssembledADT[input_t, Assembler, BitVector]
    form_val = solver.get_value(form_var.value).constant_value()
    binding_val = solver.get_value(binding_var.value).constant_value()
    form_val = log2(form_val)
    binding_val = log2(binding_val)
    print("form#", form_val)
    print("binding#", binding_val)
    binding = form_bindings[form_val][binding_val]
    res_binding = []
    bounds = set()
    for ir_path, arch_path in binding:
        if ir_path is Unbound:
            var = arch_varmap[arch_path]
            bv_val = solved_to_bv(var,solver)
            ir_path = bv_val
        else:
            bounds.add(ir_path)
        res_binding.append((ir_path,arch_path))
    bv_binding = smt_binding_to_bv_binding(res_binding)
    bv_binding = SimplifyBinding()(aadt_t,bv_binding)
    return bounds, bv_binding

def aadt_product_to_dict(value : AssembledADT):
    assert isinstance(value, AssembledADT)
    aadt_t = type(value)
    ret = OrderedDict()
    for field_name in aadt_t.adt_t.field_dict:
        ret[field_name] = value[field_name]
    return ret

def input_builder(arch_fc, binding, bound_dict : tp.Mapping["ir_path","BV"]):
    arch = arch_fc(Bit.get_family())
    input_t = arch.get_inputs()
    aadt_t = AssembledADT[input_t, Assembler, BitVector]
    arch_bindings = {}
    complete_binding = []
    for ir_path, arch_path in binding:
        if isinstance(ir_path,tuple):
            assert ir_path in bound_dict
            complete_binding.append((bound_dict[ir_path], arch_path))
        else:
            complete_binding.append((ir_path,arch_path))
    complete_binding = SimplifyBinding()(aadt_t,complete_binding)
    assert len(complete_binding)==1
    assert complete_binding[0][1] is ()
    input_val = complete_binding[0][0]

    #create dict of input values
    input_vals = OrderedDict()
    for field_name, field in aadt_t.adt_t.field_dict.items():
        input_vals[field_name] = input_val[field_name]
    return input_vals

def rebind_type(T, family):
    def _rebind_bv(T):
        return rebind_bitvector(T,AbstractBitVector,family.BitVector).rebind(AbstractBit,family.Bit,True)
    if not inspect.isclass(T):
        return T
    elif is_modified(T):
        return get_modifier(T)(rebind_type(get_unmodified(T),family,dont_rebind,do_rebind,is_magma))
    elif issubclass(T,AbstractBitVector):
        return rebind_bitvector(T,AbstractBitVector,family.BitVector)
    elif issubclass(T,AbstractBit):
        return family.Bit
    elif issubclass(T,(Product,Tuple,Sum)):
        return _rebind_bv(T)
    else:
        return T


