from peak.assembler import Assembler
from peak.assembler import AssembledADT
import typing as tp
from hwtypes import BitVector, Bit, SMTBitVector, SMTBit
from hwtypes import Product, Sum, Tuple, Enum
from hwtypes import AbstractBitVector as ABV
from collections import namedtuple
import itertools as it

class Tag: pass
class Match: pass


Form = namedtuple("Form", ["value","path_dict"])

#Constuctor for a generic smt assembled adt object
#Constructs a free variable for each leaf node and each 
# sum tag. This is returned via varmap which is a mapping
# from adt tree paths to free variables. Also included in
# the varmap is the match expressions and tags for each sum.
def generic_aadt_smt(aadt_t, path=()) -> (tp.List[tp.Mapping["path","field"]], tp.List[ABV], tp.Mapping["path",ABV]):
    if (aadt_t is SMTBit or issubclass(aadt_t, SMTBitVector)):
        #Leaf node
        bv_var = aadt_t()
        varmap = {path: bv_var}
        return [Form(value=bv_var,path_dict={})], varmap

    adt_t, assembler_t, bv_t = aadt_t.fields
    assert bv_t is SMTBitVector
    if issubclass(adt_t, Sum):
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
            sub_forms, sub_varmap = generic_aadt_smt(sub_aadt_t, path + (field,))
            #update sub_forms with current match path
            for sub_form in sub_forms:
                assert path not in sub_form.path_dict
                path_dict = {path:field,**sub_form.path_dict}
                value = aadt_t.from_fields(field,sub_form.value,tag_bv=tag)
                forms.append(Form(value=value,path_dict=path_dict))
            varmap.update(sub_varmap)
        return forms, varmap
    elif issubclass(adt_t, Product):
        forms = []
        varmap = {}

        forms_to_product = []
        #Needed to guarentee order is consistent
        adt_items =  list(adt_t.field_dict.items())
        for field_name, field in adt_items:
            sub_aadt_t = aadt_t[field_name]
            sub_forms, sub_varmap = generic_aadt_smt(sub_aadt_t, path + (field_name,))
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
    elif issubclass(adt_t, Tuple):
        forms = []
        varmap = {}

        forms_to_product = []
        for _idx, (idx, field) in enumerate(adt_t.field_dict.items()):
            assert _idx == idx
            sub_aadt_t = aadt_t[idx]
            sub_forms, sub_varmap = generic_aadt_smt(sub_aadt_t, path + (idx,))
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
    elif issubclass(adt_t, Enum):
        #Leaf node
        assembler = assembler_t(adt_t)
        bv = bv_t[assembler.width]()
        aadt_value = aadt_t(bv)
        varmap = {path: bv}
        return [Form(value=aadt_value,path_dict={})], varmap

