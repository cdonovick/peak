from peak import family_closure, family, Peak, Const
from hwtypes.adt import Enum, TaggedUnion, Product
from hwtypes import Bit, BitVector
from peak.mapper import ArchMapper

Ridx = BitVector[2]
Word = BitVector[8]
class RRInst(Product):
    class OP(Enum):
        add = 1
        mul = 2
    rs0 = Ridx
    rs1 = Ridx
    rd = Ridx

class RIInst(Product):
    class OP(Enum):
        ld_imm = 3
        add = 4
    rs = Ridx
    rd = Ridx
    imm = Word

class Inst(TaggedUnion):
    RR=RRInst
    RI=RIInst

@family_closure
def arch_fc(family):
    @family.assemble(locals(), globals())
    class Arch(Peak):
        def __call__(self, inst: Const(Inst), r0: Word, r1: Word) -> (Word, Word):
            if inst.RR.match:
                rr_inst = inst.RR.value
                if rr_inst.OP == RRInst.OP.mul:
                    return r0 * r1, r0
                else:
                    return r0 + r1, r0
            else: #inst.RI.match
                ri_inst = inst.RI.value
                imm = ri_inst.imm
                if ri_inst.OP == RIInst.OP.ld_imm:
                    return imm, r0
                else:
                    return r0 + imm, r0
    return Arch


@family_closure
def ir_add_fc(family):
    @family.assemble(locals(), globals())
    class IR(Peak):
        def __call__(self, a: Word, b: Word) -> Word:
            return a + b
    return IR

@family_closure
def ir_inc_fc(family):
    @family.assemble(locals(), globals())
    class IR(Peak):
        def __call__(self, a: Word) -> Word:
            return a + 1
    return IR

@family_closure
def ir_const_fc(family):
    @family.assemble(locals(), globals())
    class IR(Peak):
        def __call__(self, c: Const(Word)) -> Word:
            return c
    return IR

def test_basic():
    arch_mapper = ArchMapper(arch_fc)
    for ir_fc, name in (
        (ir_add_fc, "Reg-Reg Addition"),
        (ir_inc_fc, "Reg Increment"),
        (ir_const_fc, "Load Immediate"),
    ):
        ir_mapper = arch_mapper.process_ir_instruction(ir_fc, simple_formula=True)
        rewrite_rule = ir_mapper.solve('z3', external_loop=True)
        assert rewrite_rule is not None
