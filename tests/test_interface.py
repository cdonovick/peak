from examples.pe1 import PE, Inst, Bit, Data

def test_inputs():
    #Expected inputs
    expected_names = ["inst","data0", "data1", "bit0", "bit1", "bit2", "clk_en"]
    expected_types = [Inst,Data,Data,Bit,Bit,Bit,Bit]

    input_type = PE.get_inputs()
    for i, (iname,itype) in enumerate(input_type.field_dict.items()):
        assert iname == expected_names[i]
        assert itype == expected_types[i]

def test_outputs():
    #Expected inputs
    expected_names = ["alu_res", "res_p", "irq"]
    expected_types = [Data,Bit,Bit]

    assert hasattr(PE.__call__,"_peak_outputs_")
    output_type = PE.get_outputs()
    for i, (oname,otype) in enumerate(output_type.field_dict.items()):
        assert oname == expected_names[i]
        assert otype == expected_types[i]
