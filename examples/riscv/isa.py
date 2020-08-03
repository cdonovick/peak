from types import SimpleNamespace

from hwtypes.adt import Enum, Product, TaggedUnion, Sum
from hwtypes.adt_util import rebind_type

from peak import family_closure

from . import family


@family_closure(family)
def ISA_fc(family):

    Bit = family.Bit
    BitVector = family.BitVector

    Idx = family.Idx
    Word = family.Word

    # Define the layout of instruction minus tag fields (opcode/func3/func7)
    class R(Product):
        rd = Idx
        rs1 = Idx
        rs2 = Idx

    class I(Product):
        rd = Idx
        rs1 = Idx
        imm = BitVector[12]

    # For shifts
    # I would argue that is actually closer to an R type (where rs2 is treated
    # as an immiedate) than an I type. But in any event it is its own form,
    # destinct from both I and R so I don't kno why riscv calls them I type.
    class Is(Product):
        rd = Idx
        rs1 = Idx
        imm = BitVector[5]

    class S(Product):
        rs1 = Idx
        rs2 = Idx
        imm = BitVector[12]

    class U(Product):
        rd = Idx
        imm = BitVector[20]

    class B(Product):
        rs1 = Idx
        rs2 = Idx
        imm = BitVector[12]

    class J(Product):
        rd = Idx
        imm = BitVector[20]


    # define tags for func7/func3
    class ArithInst(Enum):
        ADD = Enum.Auto()
        SUB = Enum.Auto()
        SLT = Enum.Auto()
        SLTU = Enum.Auto()
        AND = Enum.Auto()
        OR = Enum.Auto()
        XOR = Enum.Auto()

    class ShiftInst(Enum):
        SLL = Enum.Auto()
        SRL = Enum.Auto()
        SRA = Enum.Auto()

    # Does not effect the encoding, but there is not
    # currently a way to union enums
    class AluInst(TaggedUnion):
        arith = ArithInst
        shift = ShiftInst

    class StoreInst(Enum):
        SB = Enum.Auto()
        SH = Enum.Auto()
        SW = Enum.Auto()
        SD = Enum.Auto()

    class LoadInst(Enum):
        LB = Enum.Auto()
        LBU = Enum.Auto()
        LH = Enum.Auto()
        LHU = Enum.Auto()
        LW = Enum.Auto()
        LWU = Enum.Auto()
        LD = Enum.Auto()

    class BranchInst(Enum):
        BEQ = Enum.Auto()
        BNE = Enum.Auto()
        BLT = Enum.Auto()
        BLTU = Enum.Auto()
        BGE = Enum.Auto()
        BGEU = Enum.Auto()

    # Define tagged Layouts
    # The types here should define the opcode field
    # and when combined with there tag define opcode/func3/func7
    class OP(Product):
        data = R
        tag = AluInst

    class OP_IMM_A(Product):
        data = I
        tag = ArithInst

    class OP_IMM_S(Product):
        data = Is
        tag = ShiftInst

    #an OP_IMM is either:
    #   OP_IMM_A (I data, ArithInst tag)
    #   OP_IMM_S (Is data, ShftInst tag)
    class OP_IMM(TaggedUnion):
        arith = OP_IMM_A
        shift = OP_IMM_S


    # LUI / AUIPC each define there own opcode so I don't merging them
    # with the tag / data style
    # HACK don't just inherit U because it breaks rebind
    class LUI(Product):
        data = U

    class AUIPC(Product):
        data = U

    # Similar to above as JAL/JALR are distinguished by opcode I don't
    # create a tagged union with JAL=J; JALR=I
    class JAL(Product):
        data = J

    class JALR(Product):
        data = I

    class Branch(Product):
        data = B
        tag = BranchInst

    class Load(Product):
        data = I
        tag = LoadInst

    class Store(Product):
        data = S
        tag = LoadInst


    # This sum type defines the opcode field
    Inst = Sum[OP, OP_IMM, LUI, AUIPC, JAL, JALR, Branch, Load, Store]

    return SimpleNamespace(**locals())
