from peak import Peak, family_closure, family, Const
from hwtypes import TypeFamily
from hwtypes.adt import TaggedUnion, Product, Enum
from hwtypes import BitVector, Bit
from peak.float import float_lib_gen, RoudningMode_utils, RoundingMode


Data = BitVector[16]

class FPU_op(Enum):
    FPAdd = 0
    FPMul = 2
    FPSqrt = 3

BFloat16 = float_lib_gen(7, 8).const_rm(RoundingMode.RDN)

@family_closure
def FPU_fc(family: TypeFamily):
    Add = BFloat16.Add_fc(family)
    Mul = BFloat16.Mul_fc(family)
    Sqrt = BFloat16.Sqrt_fc(family)

    @family.assemble(locals(), globals())
    class FPU(Peak):
        def __init__(self):
            self.add: Add = Add()
            self.mul: Mul = Mul()
            self.sqrt: Sqrt = Sqrt()

        def __call__(self, op: FPU_op, a: Data, b: Data) -> Data:
            add_out = self.add(a, b)
            mul_out = self.mul(a, b)
            sqrt_out = self.sqrt(a)
            if op == FPU_op.FPAdd:
                return add_out
            elif op == FPU_op.FPMul:
                return mul_out
            else:
                return sqrt_out

    return FPU

class ALU_op(Enum):
    Add = 1
    Sub = 2
    Or =  3
    And = 4
    XOr = 5

@family_closure
def ALU_fc(family: TypeFamily):

    @family.assemble(locals(), globals())
    class ALU(Peak):
        def __call__(self, op : ALU_op, a : Data, b : Data) -> Data:
            if op == ALU_op.Add:
                res = a + b
            elif op == ALU_op.Sub:
                res = a-b
            elif op == ALU_op.And:
                res = a & b
            elif op == ALU_op.Or:
                res = a | b
            else: # op == ALU_op.XOr:
                res = a ^ b
            return res
    return ALU


class Op(TaggedUnion):
    alu=ALU_op
    fpu=FPU_op

class Inst(Product):
    op = Op
    imm = Data
    use_imm = Bit

@family_closure
def PE_fc(family: TypeFamily):
    ALU = ALU_fc(family)
    FPU = FPU_fc(family)

    @family.assemble(locals(), globals())
    class PE(Peak):
        def __init__(self):
            self.FPU: FPU = FPU()
            self.ALU: ALU = ALU()

        def __call__(self, inst: Const(Inst), a: Data, b: Data) -> Data:
            if inst.use_imm:
                b = inst.imm
            alu_out = self.ALU(inst.op.alu.value, a, b)
            fpu_out = self.FPU(inst.op.fpu.value, a, b)
            if inst.op.alu.match:
                ret = alu_out
            else:
                ret = fpu_out
            return ret

    return PE
