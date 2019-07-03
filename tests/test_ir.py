from examples.smallir import gen_SmallIR
from examples.alu import gen_ALU
from peak.mapper import gen_mapping_ir

#This test will try to run the ir mapper function
def test_smallir():
    #arch
    arch_fc = gen_ALU()

    #IR
    SmallIR = gen_SmallIR(16)
    for name,ir_fc in SmallIR.instructions.items():
        mapping = gen_mapping_ir(ir_fc,arch_fc,1)
        assert len(list(mapping)) > 0
