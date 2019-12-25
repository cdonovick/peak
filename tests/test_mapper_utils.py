from peak.mapper.utils import Tag, Match, generic_aadt_smt
from peak.assembler.assembler import Assembler
from peak.assembler.assembled_adt import  AssembledADT
from hwtypes import BitVector, Bit, SMTBitVector, SMTBit
from hwtypes import Product, Sum, Tuple, Enum


def test_generic_aadt_smt():
    SBV = SMTBitVector
    SBit = SMTBit
    class A(Product):
        a=SBV[8]
        b=SBit
    S = Sum[A, SBV[8], SBit]
    class E(Enum):
        a=3
        b=2

    T = Tuple[S, A, SBit, E]

    expected_forms = [
        {(0,):A},
        {(0,):SBV[8]},
        {(0,):SBit},
    ]
    expected_paths = [
        (0, A,'a'),
        (0, A,'b'),
        (0, SBV[8]),
        (0, SBit),
        (0, Tag),
        (0, Match),
        (1,'a'),
        (1,'b'),
        (2,),
        (3,)
    ]


    AT = AssembledADT[T, Assembler, SBV]

    forms, varmap = generic_aadt_smt(AT)
    print("Forms")
    for form in forms:
        print("-----------------")
        print("  ",form.path_dict)
        print("  ",form.value._value_._value.serialize())
        print("  ",form.value._value_._value.simplify().serialize())
    print("Varmap")
    for path,value in varmap.items():
        if isinstance(value,dict):
            for k,v in value.items():
                print("  ",k,v._value)
        else:
            print("  ",path, value._value)
    assert 0
    #expected_paths should be exactly in varmap
    assert len(expected_paths) == len(varmap)
    for path in expected_paths:
        assert path in varmap

    #Matches should be consistent with forms
    for form in forms:
        assert form.path_dict in expected_forms
        for path,field in form.path_dict.items():
            match_path = path + (Match,)
            assert match_path in varmap
            assert field in varmap[match_path]


