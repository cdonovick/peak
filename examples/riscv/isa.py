from types import SimpleNamespace

from hwtypes.adt import Enum, Product, TaggedUnion, Sum
from hwtypes.adt_util import rebind_type

from peak import family_closure

from . import family


@family_closure(family)
def ISA_fc(family):

    Bit = family.Bit
    BitVector = family.BitVector

    IRegIdx = family.Idx
    ORegIdx = family.Idx

    class R(Product):
        rd = ORegIdx
        rs1 = IRegIdx
        rs2 = IRegIdx

    class I(Product):
        rd = ORegIdx
        rs1 = IRegIdx
        imm = BitVector[12]

    # for shifts
    class Is(Product):
        rd = ORegIdx
        rs1 = IRegIdx
        imm = BitVector[5]

    class S(Product):
        rs1 = IRegIdx
        rs2 = IRegIdx
        imm = BitVector[12]

    class U(Product):
        rd = IRegIdx
        imm = BitVector[20]

    class B(Product):
        rs1 = IRegIdx
        rs2 = IRegIdx
        imm = BitVector[12]

    class J(Product):
        rd = ORegIdx
        imm = BitVector[20]

    class ArithInst(Enum):
        ADD = Enum.Auto()
        SUB = Enum.Auto()
        SLT = Enum.Auto()
        SLTU = Enum.Auto()
        AND = Enum.Auto()
        OR = Enum.Auto()
        XOR = Enum.Auto()

    class ShftInst(Enum):
        SLL = Enum.Auto()
        SRL = Enum.Auto()
        SRA = Enum.Auto()

    class PCInst(Enum):
        LUI = Enum.Auto()
        AUIPC = Enum.Auto()

    AluInst = Sum[ArithInst, ShftInst]

    class ALUI(Product):
        data = I
        tag = ArithInst

    class ALUS(Product):
        data = Is
        tag = ShftInst

    class ALUR(Product):
        data = U
        tag = AluInst

    class ALUU(Product):
        data = U
        tag = PCInst


    class ALU(TaggedUnion):
        i = ALUI
        s = ALUS
        r = ALUR
        u = ALUU

    class JAL(J): pass
    class JALR(I): pass

    JMP = Sum[JAL, JALR]


    class BranchInst(Enum):
        BEQ = Enum.Auto()
        BNE = Enum.Auto()
        BLT = Enum.Auto()
        BLTU = Enum.Auto()
        BGE = Enum.Auto()
        BGEU = Enum.Auto()

    class Branch(Product):
        data = B
        tag = BranchInst

    class Control(TaggedUnion):
        j = JMP
        b = Branch

    class Load(Product):
        data = I
        class tag(Enum):
            LB = Enum.Auto()
            LBU = Enum.Auto()
            LH = Enum.Auto()
            LHU = Enum.Auto()
            LW = Enum.Auto()
            LWU = Enum.Auto()
            LD = Enum.Auto()


    class Store(Product):
        data = S
        class tag(Enum):
            SB = Enum.Auto()
            SH = Enum.Auto()
            SW = Enum.Auto()
            SD = Enum.Auto()

    Memory = Sum[Load, Store]

    class Inst(TaggedUnion):
        alu = ALU
        ctrl = Control
        mem = Memory


    return SimpleNamespace(**locals())
