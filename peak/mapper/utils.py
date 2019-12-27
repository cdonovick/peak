from peak.assembler import Assembler
from peak.assembler import AssembledADT
from peak.assembler import AssembledADTRecursor
import typing as tp
from hwtypes import BitVector, Bit, SMTBitVector, SMTBit
from hwtypes import Product, Sum, Tuple, Enum
from collections import namedtuple
import itertools as it

class Tag: pass
class Match: pass

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

def log2(x):
    #verify it is a power of 2
    assert x & (x-1) == 0
    return x.bit_length() - 1


##This will combine as many paths as possible together
#def simplify_bindings(aadt_t, bindings : tp.List[tp.Tuple['ir_path','arch_path']]):
#    if (aadt_t is SMTBit or issubclass(aadt_t, SMTBitVector)):
#        #Leaf node
#        assert len(bindings) == 1
#        ir_path, arch_path = list(bindings.items())[0]
#        assert arch_path is ()
#        return bindings
#
#    adt_t, assembler_t, bv_t = aadt_t.fields
#    if issubclass(adt_t, Sum):
#        #Need to find which binding
#        for ir_path, arch_path in bindings:
#            pass
#        
#        sub_bindings = {}
#        for path, value in bindings.items():
#            assert arch_path[0] == sub_field:
#            sub_bindings[arch_path[1:]] = value
#
#        sub_aadt_t = aadt_t[sub_field]
#        sub_value = bindings_to_aadt(sub_aadt_t,sub_form_path_dict,sub_bindings)
#        value = aadt_t.from_fields(sub_field,sub_value)
#        return value
#    elif issubclass(adt_t, Product):
#        #Needed to guarentee order is consistent
#        adt_items =  list(adt_t.field_dict.items())
#        bindings = {}
#        for path, value in binding.items():
#            assert path[0] in adt_t.field_dict
#            bindings.setdefault(path[0],{})
#            bindings[path[0]][path[1:]] = value
#
#        for field_name, field in adt_items:
#            sub_aadt_t = aadt_t[field_name]
#            sub_forms, sub_varmap = generic_aadt_smt(sub_aadt_t, path + (field_name,))
#            varmap.update(sub_varmap)
#            forms_to_product.append(sub_forms)
#        for sub_forms in it.product(*forms_to_product):
#            value_dict = {}
#            path_dict = {}
#            for i,sub_form in enumerate(sub_forms):
#                field_name = adt_items[i][0]
#                value_dict[field_name] = sub_form.value
#                path_dict.update(sub_form.path_dict)
#            value = aadt_t.from_fields(**value_dict)
#            forms.append(Form(value=value,path_dict=path_dict))
#        return forms, varmap
#    elif issubclass(adt_t, Tuple):
#        forms = []
#        varmap = {}
#
#        forms_to_product = []
#        for _idx, (idx, field) in enumerate(adt_t.field_dict.items()):
#            assert _idx == idx
#            sub_aadt_t = aadt_t[idx]
#            sub_forms, sub_varmap = generic_aadt_smt(sub_aadt_t, path + (idx,))
#            varmap.update(sub_varmap)
#            forms_to_product.append(sub_forms)
#        for sub_forms in it.product(*forms_to_product):
#            values = []
#            path_dict = {}
#            for sub_form in sub_forms:
#                values.append(sub_form.value)
#                path_dict.update(sub_form.path_dict)
#            value = aadt_t.from_fields(*values)
#            forms.append(Form(value=value,path_dict=path_dict))
#        return forms, varmap
#    elif issubclass(adt_t, Enum):
#        #Leaf node
#        assembler = assembler_t(adt_t)
#        bv = bv_t[assembler.width]()
#        aadt_value = aadt_t(bv)
#        varmap = {path: bv}
#        return [Form(value=aadt_value,path_dict={})], varmap


#returns binding_map
#def extract(solver, forms, form_bindings, arch_varmap, arch_fc):
#    arch = arch_fc(Bit.get_family())
#    inputs = arch.get_inputs()
#    form_val = solver.get_value(form_var.value).constant_value()
#    binding_val = solver.get_value(binding_var.value).constant_value()
#    form_val = log2(form_val)
#    binding_val = log2(binding_val)
#    print("for target", target.__name__)
#    print("form", form_val)
#    print("binding", binding_val)
#    binding = form_bindings[form_val][binding_val]
#    res_binding = []
#    bounds = set()
#    for ir_path, arch_path in binding:
#        if ir_path is Unbound:
#            var = arch_varmap[arch_path]
#            var_val = solver.get_value(var.value).constant_value()
#            ir_path = var_val
#        else:
#            bounds.add(ir_path)
#        res_binding.append((ir_path,arch_path))
#    def input_builder(bound_dict : tp.Mapping["path","BV"]):
#        arch_bindings = {}
#        for ir_path, arch_path in res_binding:
#            if isinstance(ir_path,tuple):
#                assert ir_path in bound_dict
#                arch_bindings[arch_path] = bound_dict[ir_path]
#            else:
#                arch_bindings[arch_path] = ir_path
#         return bindings_to_aadt(inputs
#    return res_binding

