from examples.PE_lut import gen_isa, gen_PE as gen_PE_lut

def test_PE_lut():
    PE_fc = gen_PE_lut(8)
    PE_fc.Py
    PE_fc.SMT
    PE_fc.Magma
    #isa = gen_isa(8).Py
    #inst = isa.Inst(
    #    alu_inst=isa.AluInst(
    #        op=isa.OP.Add,
    #        imm=isa.Data(5)
    #    ),
    #    lut = isa.LUT_t(3),
    #)
    #out = PE_fc.Py()(inst, isa.Data(3), isa.Data(1), isa.Bit(1), isa.Bit(0), isa.Bit(1))
