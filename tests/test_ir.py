from examples.smallir import gen_SmallIR
from examples.coreir import gen_CoreIR
from examples.alu import gen_ALU
from peak.mapper import ArchMapper

#This test will try to run the ir mapper function
def test_smallir():
    #arch
    arch_fc = gen_ALU()

    ALUMapper = ArchMapper(arch_fc)

    #IR
    SmallIR = gen_SmallIR(16)

    for name,ir_fc in SmallIR.instructions.items():
        mapping = list(ALUMapper.map_ir_op(ir_fc))
        print(mapping)
        assert len(mapping) > 0

def test_coreir():
    #arch
    arch_fc = gen_ALU()

    ALUMapper = ArchMapper(arch_fc)

    #IR
    CoreIR = gen_CoreIR(16)

    for name,ir_fc in CoreIR.instructions.items():
        mapping = list(ALUMapper.map_ir_op(ir_fc))
        if len(mapping)>0:
            print(name,mapping)
        else:
            print(name,"no mapping found")


test_coreir()
