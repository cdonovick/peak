from bit_vector import BitVector as BV, UIntVector, SIntVector

__all__ =  ['BV', 'Bit', 'UInt', 'SInt', 'Bits', 'is_bits']

def Bits(n):
    class _Bits(BV):
        def __init__(self, i):
            super().__init__(i,n)
    return _Bits

def UInt(n):
    class _Bits(UIntVector):
        def __init__(self, i):
            super().__init__(i,n)
    return _Bits

def SInt(n):
    class _Bits(SIntVector):
        def __init__(self, i):
            super().__init__(i,n)
    return _Bits

Bit = Bits(1)

def is_bits(bits):
    return isinstance(bits,BV)
