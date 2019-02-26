from .. import Bits

# Types for LUT operations
Bit = Bits(1)
LUT = Bits(8)

# Implement a 3-bit LUT
def lut( lut:LUT, bit0:Bit, bit1:Bit, bit2:Bit) -> Bit:
    i = (int(bit2)<<2) | (int(bit1)<<1) | int(bit0)
    return Bit(lut & (1 << i))

