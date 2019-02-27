from peak.pe1 import PE, Inst, Bit, Data


def test_inputs():
    #Expected inputs
    expected_names = ["inst", "data0", "data1", "bit0", "bit1", "bit2", "clk_en"]
    expected_types = [Inst,Data,Data,Bit,Bit,Bit,Bit]

    assert hasattr(PE.__call__,"__peak_inputs__")
    inputs = PE.__call__.__peak_inputs__
    for i, (iname,itype) in enumerate(inputs.items()):
        assert iname == expected_names[i]
        assert itype == expected_types[i]

def test_outputs():
    #Expected inputs
    expected_names = ["alu_res", "res_p", "irq"]
    expected_types = [Data,Bit,Bit]

    assert hasattr(PE.__call__,"__peak_outputs__")
    outputs = PE.__call__.__peak_outputs__
    for i, (oname,otype) in enumerate(outputs.items()):
        assert oname == expected_names[i]
        assert otype == expected_types[i]

