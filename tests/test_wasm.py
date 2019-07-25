from examples.wasm import WASM
from hwtypes import BitVector, Bit


Data = BitVector[32]

def test_i32_rotl():
    rotl_class = WASM.instructions['i32_rotl']
    assert rotl_class.get_inputs().field_dict == dict(in0=Data,in1=Data)
    assert rotl_class.get_outputs().field_dict == dict(out=Data)

    #directed test

    in0 = Data(0x12345678)
    in1 = Data(8)
    out = Data(0x34567812)
    assert rotl_class()(in0,in1) == out

