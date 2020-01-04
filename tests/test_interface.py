from peak.pe1 import PE, Inst, Bit, Data
from hwtypes.adt import Product

def test_inputs():
    #Expected inputs
    expected_names = ["inst", "data0", "data1", "bit0", "bit1", "bit2", "clk_en"]
    expected_types = [Inst,Data,Data,Bit,Bit,Bit,Bit]

    input_t = PE.input_t
    assert issubclass(input_t, Product)
    for i, (iname,itype) in enumerate(input_t.field_dict.items()):
        assert iname == expected_names[i]
        assert itype == expected_types[i]

def test_outputs():
    #Expected inputs
    expected_names = ["alu_res", "res_p", "irq"]
    expected_types = [Data,Bit,Bit]

    output_t = PE.output_t
    assert issubclass(output_t, Product)
    for i, (oname,otype) in enumerate(output_t.field_dict.items()):
        assert oname == expected_names[i]
        assert otype == expected_types[i]

