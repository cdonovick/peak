import examples.fp_pe as fp
from hwtypes import SMTBitVector as SBV, SMTBit as SBit
from peak.family import SMTFamily, BlackBox

def test_fp_pe_bb():
    PE = fp.PE_fc.Py
    pe = PE()
    paths_to_bbs = BlackBox.get_black_boxes(pe)
    for path in (
        ("FPU", "add"),
        ("FPU", "mul"),
        ("FPU", "sqrt"),
    ):
        assert path in paths_to_bbs
        bb_inst = paths_to_bbs[path]
        assert bb_inst is BlackBox.get_black_box(pe, path)
        assert isinstance(bb_inst, BlackBox)


def test_fp_pe_py():

    PE = fp.PE_fc.Py
    pe = PE()
    paths_to_bbs = BlackBox.get_black_boxes(pe)
    for bb in paths_to_bbs.values():
        bb._set_outputs(fp.Data(0))
    inst = fp.Inst(
        op=fp.Op(alu=fp.ALU_op.Add),
        imm=fp.Data(10),
        use_imm=fp.Bit(1)
    )
    val = pe(inst, fp.Data(5), fp.Data(2))
    assert val == fp.Data(15)
    assert paths_to_bbs[("FPU", "add")]._get_inputs() == (fp.Data(5), fp.Data(10))
    assert paths_to_bbs[("FPU", "mul")]._get_inputs() == (fp.Data(5), fp.Data(10))
    assert paths_to_bbs[("FPU", "sqrt")]._get_inputs() == (fp.Data(5),)

def test_fp_pe_smt():
    pe = fp.PE_fc.SMT()
    AInst = SMTFamily().get_adt_t(fp.Inst)
    inst = AInst.from_fields(
        op=AInst.op(
            fpu=AInst.op.fpu(fp.FPU_op.FPAdd)
        ),
        imm=SBV[16](10),
        use_imm=SBit(name='ui')
    )
    paths_to_bbs = BlackBox.get_black_boxes(pe)
    for bb in paths_to_bbs.values():
        bb._set_outputs(SBV[16]())
    val = pe(inst, SBV[16](name='a'), SBV[16](2))
    for bb in paths_to_bbs.values():
        bb_inputs = bb._get_inputs()
