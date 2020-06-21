from examples.PE_lut import gen_isa, gen_PE as gen_PE_lut

def test_PE_lut():
    PE_fc = gen_PE_lut(8)
    PE_fc.Py
    PE_fc.SMT
    PE_fc.Magma

