from peak.mapper.utils import _TAG, Match, SMTForms
from peak.assembler.assembler import Assembler
from peak.assembler.assembled_adt import  AssembledADT
from hwtypes import SMTBitVector as SBV, SMTBit as SBit
from hwtypes import Product, Sum, Tuple, Enum


def test_SMTForms():
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
        (0, _TAG),
        (0, Match),
        (1,'a'),
        (1,'b'),
        (2,),
        (3,)
    ]

    def free_var(aadt_t):
        adt_t, assembler_t, bv_t = aadt_t.fields
        assembler = assembler_t(adt_t)
        return aadt_t(SBV[assembler.width]())
    AT = AssembledADT[T, Assembler, SBV]
    aadt_val = free_var(AT)
    for value in (None, aadt_val):
        forms, varmap, _ = SMTForms()(AT, value=value)
        if value is not None:
            for form in forms:
                assert form.value == value

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

