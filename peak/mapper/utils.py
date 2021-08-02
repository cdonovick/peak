from collections import namedtuple, OrderedDict
from functools import wraps
import itertools as it
import operator
import typing as tp

from hwtypes import BitVector, Bit, SMTBitVector, SMTBit
from hwtypes.adt import Product, Sum, Tuple, TaggedUnion
from hwtypes.adt_util import rebind_type

import pysmt.shortcuts as smt

from peak.assembler import Assembler
from peak.assembler import AssembledADT
from peak.assembler import AssembledADTRecursor
from peak.assembler import _TAG
from peak import family

class Match: pass
class Unbound: pass
Form = namedtuple("Form", ["value", "path_dict", "varmap"])


# SMTForms Constrcuts all the Forms for a particular AssemledADT type
# A Form represents a single 'product' when the ADT type is simplified to 'Sum of Products' form.
# Form contains
#   value: constructed value from varmap if value is none;
#         otherwise original value
#   path_dict: all the sum decisions that uniquely identify that particular form
#   varmap: contains
#      values of all the leaf nodes (free vars if value is none)
#      tags of all the sum types (free vars if value is none)
#      match expressions for all possible sum choices
class SMTForms(AssembledADTRecursor):
    def __call__(self, aadt_t, path=(), value=None) -> (tp.List[Form], tp.Mapping["path", SMTBitVector]):
        if value is not None:
            assert isinstance(value, aadt_t)
        return super().__call__(aadt_t, path=path, value=value)

    def bv(self, aadt_t, path, value):
        #Leaf node
        if value is None:
            #bv_value = aadt_t(prefix=str(path))
            bv_value = aadt_t(prefix=".".join(str(n) for n in path))
        else:
            bv_value = value
        varmap = {path: bv_value}
        return [Form(value=bv_value, path_dict={}, varmap=varmap)], varmap, bv_value

    def enum(self, aadt_t, path, value):
        #Leaf node
        if value is None:
            adt_t, assembler_t, bv_t = aadt_t.fields
            assembler = assembler_t(adt_t)
            bv_value = bv_t[assembler.width](prefix=".".join(str(n) for n in path))
            aadt_value = aadt_t(bv_value)
        else:
            assert isinstance(value, aadt_t)
            bv_value = value._value_
            aadt_value = value
        varmap = {path: bv_value}
        return [Form(value=aadt_value, path_dict={}, varmap=varmap)], varmap, aadt_value

    def sum(self, aadt_t, path, value):
        adt_t, assembler_t, bv_t = aadt_t.fields
        assembler = aadt_t._assembler_
        #Create _TAG
        if value is None:
            tag = SMTBitVector[assembler.tag_width]()
        else:
            tag = value[_TAG]

        field_dict = {}
        forms = []
        varmap = {}
        varmap[path + (_TAG,)] = tag
        varmap[path + (Match,)] = {}
        fields = list(adt_t.fields)
        for field in fields:
            #field_tag_value = assembler.assemble_tag(field, bv_t)
            #tag_match = (tag==field_tag_value)
            sub_aadt_t = aadt_t[field]
            if value is None:
                sub_value = None
            else:
                sub_value = value[field].value
            sub_forms, sub_varmap, _sub_value = self(sub_aadt_t, path=path + (field,), value=sub_value)
            _value = aadt_t.from_fields(field, _sub_value, tag_bv=tag)
            #update sub_forms with current match path
            for sub_form in sub_forms:
                assert path not in sub_form.path_dict
                path_dict = {path:field, **sub_form.path_dict}
                if value is None:
                    form_value = aadt_t.from_fields(field, sub_form.value, tag_bv=tag)
                else:
                    form_value = value
                forms.append(Form(value=form_value, path_dict=path_dict, varmap=sub_form.varmap))
            match_cond = _value[field].match
            varmap[path + (Match,)][field] = match_cond
            field_dict[field] = (_value, match_cond)
            varmap.update(sub_varmap)

        #Create a large ite chain
        items = list(field_dict.items())
        sum_value = items[0][1][0]
        for field, (value, cond) in items[1:]:
            sum_value = cond.ite(value, sum_value)

        return forms, varmap, sum_value

    def tagged_union(self, aadt_t, path, value):
        adt_t, assembler_t, bv_t = aadt_t.fields
        assembler = aadt_t._assembler_
        #Create _TAG
        if value is None:
            tag_prefix = ".".join([str(p) for p in path] + ["TAG"])
            tag = SMTBitVector[assembler.tag_width](prefix=tag_prefix)
        else:
            tag = value[_TAG]

        field_dict = {}
        forms = []
        varmap = {}
        varmap[path + (_TAG,)] = tag
        varmap[path + (Match,)] = {}
        for field_name, field in adt_t.field_dict.items():
            #field_tag_value = assembler.assemble_tag(field, bv_t)
            #tag_match = (tag==field_tag_value)
            sub_aadt_t = getattr(aadt_t, field_name)
            if value is None:
                sub_value = None
            else:
                sub_value = value[field].value

            sub_forms, sub_varmap, _sub_value = self(sub_aadt_t, path=path + (field_name,), value=sub_value)
            _value = aadt_t.from_fields(tag_bv=tag, **{field_name: _sub_value})
            #update sub_forms with current match path
            for sub_form in sub_forms:
                assert path not in sub_form.path_dict
                path_dict = {path:field_name, **sub_form.path_dict}
                if value is None:
                    form_value = aadt_t.from_fields(tag_bv=tag, **{field_name: sub_form.value})
                else:
                    form_value = value
                forms.append(Form(value=form_value, path_dict=path_dict, varmap=sub_form.varmap))
            match_cond = getattr(_value, field_name).match
            varmap[path + (Match,)][field_name] = match_cond
            field_dict[field_name] = (_value, match_cond)
            varmap.update(sub_varmap)

        #Create a large ite chain
        items = list(field_dict.items())
        ta_value = items[0][1][0]
        for field, (value, cond) in items[1:]:
            ta_value = cond.ite(value, ta_value)
        return forms, varmap, ta_value

    #TODO lots of common code between product and tuple
    def product(self, aadt_t, path, value):
        adt_t, assembler_t, bv_t = aadt_t.fields
        forms = []
        varmap = {}


        field_to_value = {}
        forms_to_product = []
        #Needed to guarentee order is consistent
        adt_items =  list(adt_t.field_dict.items())
        for field_name, field in adt_items:
            sub_aadt_t = aadt_t[field_name]
            if value is None:
                sub_value = None
            else:
                sub_value = value[field_name]
            sub_forms, sub_varmap, _sub_value = self(sub_aadt_t, path=path + (field_name,), value=sub_value)
            field_to_value[field_name] = _sub_value
            varmap.update(sub_varmap)
            forms_to_product.append(sub_forms)

        p_value = aadt_t.from_fields(**field_to_value)
        for sub_forms in it.product(*forms_to_product):
            value_dict = {}
            path_dict = {}
            form_varmap = {}
            for i, sub_form in enumerate(sub_forms):
                field_name = adt_items[i][0]
                value_dict[field_name] = sub_form.value
                path_dict.update(sub_form.path_dict)
                form_varmap.update(sub_form.varmap)
            value = aadt_t.from_fields(**value_dict)
            forms.append(Form(value=value, path_dict=path_dict, varmap=form_varmap))

        return forms, varmap, p_value

    def tuple(self, aadt_t, path, value):
        adt_t, assembler_t, bv_t = aadt_t.fields
        forms = []
        varmap = {}

        values = []
        forms_to_product = []
        for _idx, (idx, field) in enumerate(adt_t.field_dict.items()):
            assert _idx == idx
            sub_aadt_t = aadt_t[idx]
            if value is None:
                sub_value = None
            else:
                sub_value = value[idx]
            sub_forms, sub_varmap, _sub_value = self(sub_aadt_t, path=path + (idx,), value=sub_value)
            values.append(_sub_value)
            varmap.update(sub_varmap)
            forms_to_product.append(sub_forms)
        t_value = aadt_t.from_fields(*values)
        for sub_forms in it.product(*forms_to_product):
            values = []
            path_dict = {}
            form_varmap = {}
            for sub_form in sub_forms:
                values.append(sub_form.value)
                path_dict.update(sub_form.path_dict)
                form_varmap.update(sub_form.varmap)
            value = aadt_t.from_fields(*values)
            forms.append(Form(value=value, path_dict=path_dict, varmap=form_varmap))
        return forms, varmap, t_value

def check_leaf(required=False):
    def dec(f):
        @wraps(f)
        def method(self, aadt_t, binding):
            if required:
                assert len(binding) == 1
                assert binding[0][1] == ()
            if len(binding)==1 and binding[0][1] == ():
                return binding
            return f(self, aadt_t, binding)
        return method
    return dec

#This will combine any sibling nodes together which are constants
#resulting in the most simplified form of the binding
class SimplifyBinding(AssembledADTRecursor):
    def __call__(self, aadt_t, binding : tp.List[tp.Tuple['ir_path', 'arch_path']]):
        return super().__call__(aadt_t, binding)

    @check_leaf(required=True)
    def bv(self, aadt_t, binding):
        pass

    @check_leaf(required=True)
    def enum(self, aadt_t, binding):
        pass

    @check_leaf(required=False)
    def sum(self, aadt_t, binding):
        builder = aadt_t.from_fields
        return self.tagged_or_sum(aadt_t, binding, operator.getitem, builder)


    @check_leaf(required=False)
    def tagged_union(self, aadt_t, binding):
        def builder(tag, value):
            return aadt_t.from_fields(**{tag: value})
        return self.tagged_or_sum(aadt_t, binding, getattr, builder)

    def tagged_or_sum(self, aadt_t, binding, getter, builder):
        adt_t, assembler_t, bv_t = aadt_t.fields
        #Find the correct field
        sub_field = binding[0][1][0]
        sub_binding = []
        for ir_path, arch_path in binding:
            assert arch_path[0] == sub_field
            sub_binding.append((ir_path, arch_path[1:]))
        sub_aadt_t = getter(aadt_t, sub_field)

        simplified_binding = self(sub_aadt_t, sub_binding)

        #Completely simplified if only one binding and ir_path is a value instead of a path
        if len(simplified_binding)==1 and not isinstance(simplified_binding[0][0], tuple):
            sub_value, arch_path = simplified_binding[0]
            assert arch_path == ()
            value = builder(sub_field, sub_value)
            return [(value, ())]
        else:
            return [(ir_path, (sub_field,) + arch_path) for ir_path, arch_path in simplified_binding]


    def product_or_tuple(self, aadt_t, binding, *, is_product):
        adt_t, assembler_t, bv_t = aadt_t.fields
        sub_binding_dict = {}
        for ir_path, arch_path in binding:
            field_name = arch_path[0]
            assert field_name in adt_t.field_dict
            sub_binding_dict.setdefault(field_name, [])
            sub_binding_dict[field_name].append((ir_path, arch_path[1:]))
        assert len(sub_binding_dict) == len(adt_t.field_dict)

        simplify = True
        simplified_binding_dict = {}
        for field_name, sub_binding in sub_binding_dict.items():
            simplified_binding = self(aadt_t[field_name], sub_binding)
            simplified_binding_dict[field_name] = simplified_binding
            simplify &= len(simplified_binding)==1 and not (isinstance(simplified_binding[0][0], tuple) or simplified_binding[0][0] is Unbound)

        if simplify:
            value_dict = {field_name:b[0][0] for field_name, b in simplified_binding_dict.items()}
            if is_product:
                value = aadt_t.from_fields(**value_dict)
            else: #is tuple
                values = [v for _, v in sorted(value_dict.items())]
                value = aadt_t.from_fields(*values)
            return [(value, ())]
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
    assert x !=0 and (x & (x-1) == 0)
    return x.bit_length() - 1

def solved_to_bv(var, solver):
    smt_var = solver.get_value(var.value)
    assert smt_var.is_constant()
    solver_value = smt_var.constant_value()
    if isinstance(var, SMTBit):
        return Bit(solver_value)
    else:
        return BitVector[var.size](solver_value)

def rebind_value(val, _family):
    if isinstance(val, family.PyFamily().BitVector):
        return _family.BitVector[val.size](val.value)
    elif isinstance(val, family.PyFamily().Bit):
        return _family.Bit(val)
    elif isinstance(val, family.SMTFamily().BitVector):
        if not val._value_.is_constant():
            raise ValueError("Cannot convert non-const SMT var to Py")
        return _family.BitVector[val.size](val._value_.constant_value())
    elif isinstance(val, family.SMTFamily().Bit):
        if not val._value_.is_constant():
            raise ValueError("Cannot convert non-const SMT var to Py")
        return _family.Bit(val._value_.constant_value())
    else:
        raise ValueError(f"Cannot rebind value: {val}")

#returns a binding where all aadt values are changed to family
def rebind_binding(binding, _family):
    ret_binding = []
    for ir_path, arch_path in binding:
        arch_path = arch_path[:-1] + (rebind_type(arch_path[-1], _family),)
        if not (isinstance(ir_path, tuple) or ir_path is Unbound):
            ir_path = rebind_value(ir_path, _family)
        ret_binding.append((ir_path, arch_path))
    return ret_binding

def aadt_product_to_dict(value : AssembledADT):
    assert isinstance(value, AssembledADT)
    aadt_t = type(value)
    ret = OrderedDict()
    for field_name in aadt_t.adt_t.field_dict:
        ret[field_name] = value[field_name]
    return ret

def _sort_by_t(path2t : tp.Mapping[tuple, "adt"]) ->tp.Mapping["adt", tp.List[tuple]]:

    t2path = {}
    for tup, t in path2t.items():
        t2path.setdefault(t, []).append(tup)

    return t2path



def create_bindings(arch_flat: dict, ir_flat: dict):
    arch_by_t = _sort_by_t(arch_flat)
    ir_by_t = _sort_by_t(ir_flat)
    #check early out
    if not all((ir_type in arch_by_t) for ir_type in ir_by_t):
        return []

    possible_matching = OrderedDict()
    for arch_type, arch_paths in arch_by_t.items():
        ir_paths = ir_by_t.setdefault(arch_type, [])

        #ir_poss represents all the possible inputs that could be bound to each arch_input
        ir_poss = tuple(ir_paths) + (Unbound,)
        #Now ir_poss has all the possible mappings for each arch_path

        #Filter out some bindings
        #Only count bindings where each ir is represented exactly once
        #Might want to decrease this restriction to find things like (0 -> x^x)
        #TODO could have this customizable 
        def filt(poss):
            ret = True
            for ir_path in ir_paths:
                num_ir = poss.count(ir_path)
                ret = ret and (num_ir==1)
                #early out
                if ret is False:
                    return False
            return ret
        type_bindings = []

        for ir_match in filter(filt, it.product(*[ir_poss for _ in range(len(arch_paths))])):

            type_bindings.append(list(zip(ir_match, arch_paths)))
        possible_matching[arch_type] = type_bindings
    bindings = []

    for l in it.product(*possible_matching.values()):
        bindings.append(list(it.chain(*l)))
    return bindings

def _pretty_path(path):
    if path is Unbound:
        return "Unbound"
    elif isinstance(path, tuple):
        return ".".join(str(p) for p in path)
    else:
        return str(path)

def pretty_print_binding(binding, printer=print):
    printer("(")
    for ir_path, arch_path in binding:
        printer(f"  {_pretty_path(ir_path)} <=> {_pretty_path(arch_path)}")
    printer(")")
