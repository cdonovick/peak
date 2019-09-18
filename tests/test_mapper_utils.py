from peak.mapper.utils import Tag, generic_aadt_smt
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

    AT = AssembledADT[T, Assembler, SBV]

    AT_value, varmap = generic_aadt_smt(AT)
    expected_paths = [
        (0, A,'a'),
        (0, A,'b'),
        (0, SBV[8]),
        (0, SBit),
        (0, Tag),
        (1,'a'),
        (1,'b'),
        (2,),
        (3,)
    ]
    assert len(expected_paths) == len(varmap)
    for path in expected_paths:
        assert path in varmap
