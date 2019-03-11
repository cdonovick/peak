from hwtypes import BitVector, Bit

LUT_t = BitVector[8]
_IDX_t = BitVector[3]

def lut( lut:LUT_t, bit0:Bit, bit1:Bit, bit2:Bit) -> Bit:
    i = _IDX_t([bit0, bit1, bit2])
    i = i.zext(5)
    return ((lut >> i) & 1)[0]

