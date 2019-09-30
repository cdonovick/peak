from peak.assembler import Assembler
from peak.assembler import AssembledADT
import typing as tp
from hwtypes import BitVector, Bit, SMTBitVector, SMTBit
from hwtypes import Product, Sum, Tuple, Enum

#Constructs a sum object from all types by creating an ite chain
#Also returns a map of match expressions and the tag itself
def sum_all_subfields(aadt_t, subfields : tp.Mapping) -> (AssembledADT, tp.Mapping, SMTBitVector):
    adt_t, assembler_t, bv_t = aadt_t.fields
    assembler = assembler_t(adt_t)
    assert issubclass(adt_t, Sum)
    assert bv_t is SMTBitVector
    assert len(adt_t.fields) == len(subfields)

    sum_values = {field: aadt_t.from_fields(field, value) for field, value in subfields.items()}

    #Create Tag
    tag_t = SMTBitVector[assembler.tag_width]
    tag = tag_t()
    #create final BitVector representing the sum
    bv_val = SMTBitVector[assembler.width](0)
    for field, sum_value in sum_values.items():
        tag_val = assembler._tag_asm(field)
        bv_val = (tag==tag_t(tag_val)).ite(sum_value._value_, bv_val)
    aadt_val = aadt_t(bv_val)
    matches = {field: aadt_val[field].match for field in adt_t.fields}
    return aadt_val, matches, tag

class Tag: pass
class Match: pass

#Constuctor for a generic smt assembled adt object
#Constructs a free variable for each leaf node and each 
# sum tag. This is returned via varmap which is a mapping
# from adt tree paths to free variables. Also included in
# the varmap is the match expressions and tags for each sum.
def generic_aadt_smt(aadt_t, path=()):
    if (aadt_t is SMTBit or issubclass(aadt_t, SMTBitVector)):
        #Leaf node
        bv = aadt_t()
        varmap = {path: bv}
        return bv, varmap
    adt_t, assembler_t, bv_t = aadt_t.fields
    assert bv_t is SMTBitVector
    if issubclass(adt_t, Sum):
        varmap = {}
        subfields = {}
        for field in adt_t.fields:
            sub_aadt_t = aadt_t[field]
            sub_aadt_value, sub_varmap = generic_aadt_smt(sub_aadt_t, path + (field,))
            subfields[field] = sub_aadt_value
            varmap.update(sub_varmap)
        sum_value, matches, tag = sum_all_subfields(aadt_t, subfields)
        varmap[path + (Tag,)] = tag
        varmap[path + (Match,)] = matches
        return sum_value, varmap
    elif issubclass(adt_t, Product):
        varmap = {}
        value_dict = {}
        for field_name, field in adt_t.field_dict.items():
            sub_aadt_t = aadt_t[field_name]
            sub_aadt_value, sub_varmap = generic_aadt_smt(sub_aadt_t, path + (field_name,))
            value_dict[field_name] = sub_aadt_value
            varmap.update(sub_varmap)
        prod_value = aadt_t.from_fields(**value_dict)
        return prod_value, varmap
    elif issubclass(adt_t, Tuple):
        varmap = {}
        values = []
        for _idx, (idx, field) in enumerate(adt_t.field_dict.items()):
            assert _idx == idx
            sub_aadt_t = aadt_t[idx]
            sub_aadt_value, sub_varmap = generic_aadt_smt(sub_aadt_t, path + (idx,))
            values.append(sub_aadt_value)
            varmap.update(sub_varmap)
        tup_value = aadt_t.from_fields(*values)
        return tup_value, varmap
    elif issubclass(adt_t, Enum):
        #Leaf node
        assembler = assembler_t(adt_t)
        bv = bv_t[assembler.width]()
        aadt_value = aadt_t(bv)
        varmap = {path: bv}
        return aadt_value, varmap

