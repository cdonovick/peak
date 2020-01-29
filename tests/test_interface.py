from examples.pe1 import PE, Inst, Bit, Data
from hwtypes.adt import Product, Sum
from hwtypes import BitVector, SMTBitVector
from peak import Peak, name_outputs, family_closure
import pytest

def test_inputs():
    #Expected inputs
    expected_names = ["inst", "data0", "data1", "bit0", "bit1", "bit2", "clk_en"]
    expected_types = [Inst, Data, Data, Bit, Bit, Bit, Bit]

    input_t = PE.input_t
    assert issubclass(input_t, Product)
    for i, (iname, itype) in enumerate(input_t.field_dict.items()):
        assert iname == expected_names[i]
        assert itype == expected_types[i]

def test_outputs():
    #Expected inputs
    expected_names = ["alu_res", "res_p", "irq"]
    expected_types = [Data, Bit, Bit]

    output_t = PE.output_t
    assert issubclass(output_t, Product)
    for i, (oname, otype) in enumerate(output_t.field_dict.items()):
        assert oname == expected_names[i]
        assert otype == expected_types[i]

def test_family_closure():
    #family_closure needs single argument
    with pytest.warns(Warning):
        @family_closure
        def fc(family, otherarg):
            class A(Peak): pass
            return A

    #family_closure needs to return a peak class
    with pytest.warns(Warning):
        @family_closure
        def fc(family):
            return 5
        cls = fc(Bit.get_family())

    #family_closure needs to return only a single peak class
    with pytest.warns(Warning):
        @family_closure
        def fc(family):
            class A(Peak): pass
            return A, A
        cls, _ = fc(Bit.get_family())

    #family closure can return other objects, as long as there is only one peak class
    with pytest.warns(None) as record:
        @family_closure
        def fc(family):
            S = Sum[int,str]
            class A(Peak): pass
            return A, S
        cls, _ = fc(Bit.get_family())
    assert len(record)==0

    @family_closure
    def PE_fc(family):
        Word = family.BitVector[16]
        class PE(Peak):
            @name_outputs(out=Word)
            def __call__(self, in0:Word, in1:Word):
                return in0 + in1
        return PE

    assert isinstance(PE_fc, family_closure)

    for family in (BitVector.get_family(), SMTBitVector.get_family()):
        #Test caching
        assert PE_fc(family) is PE_fc(family)

        #Test storing the family closure in the Peak class
        assert PE_fc(family)._fc_ is PE_fc

def test_unsafe():
    def fc(family):
        class A(Peak, unsafe=True):
            def __call__(self, val):
                return val
    with pytest.warns(None) as record:
        fc(Bit.get_family())
    assert len(record) == 0





