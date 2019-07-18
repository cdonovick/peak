from examples.smallir import gen_SmallIR
from peak.irs import gen_CoreIR
from peak.ir import IR
from examples.alu import gen_ALU
from examples.simple_sum import simple_sum_fc
from peak.mapper import ArchMapper, binding_pretty_print
from hwtypes import BitVector, SMTBitVector, Bit, SMTBit
from hwtypes import AbstractBitVector as ABV
from hwtypes import AbstractBit
from hwtypes.adt import Product, Sum
import itertools as it

def test_add_peak_instruction():
    class Input(Product):
        a = ABV[16]
        b = ABV[16]
        c = AbstractBit

    class Output(Product):
        x = ABV[16]
        y = AbstractBit

    ir = IR()
    def fun(a,b,c):
        return c.ite(a,b),c

    ir.add_peak_instruction("simple",Input,Output,fun)

    assert "simple" in ir.instructions
    fc = ir.instructions["simple"]
    try:
        bv_instr = fc(BitVector.get_family())()
        BV16 = BitVector[16]
        x,y = bv_instr(BV16(5),BV16(6),Bit(1))
        assert x == BV16(5)
        assert y == Bit(1)
    except:
        assert 0

#This test will try to run the ir mapper function
def test_smallir():
    #arch
    arch_fc = gen_ALU()

    ALUMapper = ArchMapper(arch_fc)

    #IR
    SmallIR = gen_SmallIR(16)

    has_mappings = ("Not","Neg","Add","Sub","And")
    for name,ir_fc in SmallIR.instructions.items():
        mapping = list(ALUMapper.map_ir_op(ir_fc))
        has_mapping = len(mapping) > 0
        assert has_mapping == (name in has_mappings)

#test_smallir()

def test_smallir_custom_enum():
    #arch
    arch_fc = gen_ALU()

    ALUOP = arch_fc(SMTBitVector.get_family()).__call__._peak_inputs_["inst"].alu_op
    def filter_out_and(t):
        for k in filter(lambda inst: inst !=ALUOP.And,ALUOP.enumerate()):
            yield k
    ALUMapper = ArchMapper(arch_fc,custom_enumeration={ALUOP:filter_out_and})

    #IR
    SmallIR = gen_SmallIR(16)

    #And should not have mapping
    has_mappings = ("Not","Neg","Add","Sub")
    for name,ir_fc in SmallIR.instructions.items():
        mapping = list(ALUMapper.map_ir_op(ir_fc))
        has_mapping = len(mapping) > 0
        assert has_mapping == (name in has_mappings)


def test_coreir():
    #arch
    arch_fc = gen_ALU()

    ALUMapper = ArchMapper(arch_fc)

    #IR
    CoreIR = gen_CoreIR(16)

    has_mappings = ("const","add","sub","and_","or_","xor","wire","not_","neg")

    for name,ir_fc in CoreIR.instructions.items():
        mapping = list(ALUMapper.map_ir_op(ir_fc))
        has_mapping = len(mapping) > 0
        assert has_mapping == (name in has_mappings)


def test_simple_sum():
    #arch
    arch_fc = simple_sum_fc

    SSMapper = ArchMapper(arch_fc)

    #IR
    SmallIR = gen_SmallIR(16)

    gold_mappings = {
        "Not":1,
        "Neg":1,
        "Add":36,
        "Sub":3
    }
    for name,ir_fc in SmallIR.instructions.items():
        if name != "Add":
            continue
        mappings = list(SSMapper.map_ir_op(ir_fc,max_mappings=100))
        num_mappings = len(mappings)
        print(name,num_mappings,gold_mappings.setdefault(name,0))
        #assert num_mappings == gold_mappings.setdefault(name,0)
        print(f"mappings found for {name} {{")
        for mi,mapping in enumerate(mappings):
            print(f"  Mapping {mi}")
            binding_pretty_print(mapping['input_binding'],ts="    ")
        print("-------")
        print("}")

test_simple_sum()
