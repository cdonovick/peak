import functools as ft
import operator
import typing as tp

from hwtypes import AbstractBitVector, AbstractBit

def _issubclass(sub , parent : type) -> bool:
    try:
        return issubclass(sub, parent)
    except TypeError:
        return False


_RANGE_COST = 1.1
_validator_cache = {}
def _gen_is_valid(
        opcodes: tp.Sequence[int],
        width: int) -> tp.Callable[[AbstractBitVector], AbstractBit]:
    '''
    Generates an is_valid function from a set of opcodes.
    '''
    opcodes = tuple(sorted(opcodes))
    try:
        return _validator_cache[opcodes]
    except KeyError:
        pass

    min_op = opcodes[0]
    max_op = opcodes[-1]

    is_range = opcodes == tuple(range(min_op, max_op + 1))
    implicit_lb = (min_op == 0)
    implicit_ub = (max_op == ((1 <<  width) - 1))

    # check if all possible opcodes are valid
    if is_range and implicit_lb and implicit_ub:
        def is_valid(opcode: AbstractBitVector) -> AbstractBit:
            return opcode.get_family().Bit(1)
        return _validator_cache.setdefault(opcodes, is_valid)

    # The naive approach
    def is_valid(opcode: AbstractBitVector) -> AbstractBit:
        return ft.reduce(operator.or_,
                (opcode == code for code in opcodes),
                opcode.get_family().Bit(0))

    if len(opcodes) < 3:
        # No point in doing anything fancy for less than 3 options
        return _validator_cache.setdefault(opcodes, is_valid)

    # Check for single contiguous range
    if is_range:
        if implicit_lb:
            # only need upper bound
            def is_valid(opcode: AbstractBitVector) -> AbstractBit:
                return opcode <= max_op
        elif implicit_ub:
            def is_valid(opcode: AbstractBitVector) -> AbstractBit:
                return min_op <= opcode
        else:
            def is_valid(opcode: AbstractBitVector) -> AbstractBit:
                return (min_op <= opcode) & (opcode <= max_op)

    # Check for 1 hot encoding
    elif all(x & (x - 1) == 0 for x in opcodes):
        # figure out the set of of 1 hot values (and 0)
        # that are not valid
        invalid = []

        if 0 not in opcodes:
            invalid.append(0)

        x = 1
        while x < (1 << width):
            if x not in opcodes:
                invalid.append(x)
            x <<= 1

        # if enumerating the set of invalids is cheaper
        # then just enumerating the opcodes do so
        # otherwise just stick to the basic version.
        if len(invalid) < len(opcodes):
            def is_valid(opcode: AbstractBitVector) -> AbstractBit:
                is_one_hot = (opcode & (opcode - 1)) == 0
                is_not_invlaid = ft.reduce(
                                    operator.and_,
                                    (opcode != b for b in invalid),
                                    opcode.get_family().Bit(1)
                                    )


                return is_one_hot & is_not_invlaid

    # Check for multiple ranges
    else:
        range_validators = []
        lb = min_op
        for i, j in zip(opcodes, opcodes[1:]):
            if j == i + 1:
                continue

            range_validators.append(_gen_is_valid(range(lb, i+1), width))
            lb = j

        assert j == max_op
        assert i == opcodes[-2]
        if j == i+1:
            range_validators.append(_gen_is_valid(range(lb, j+1), width))
        elif j == lb:
            range_validators.append(_gen_is_valid(range(lb, lb+1), width))
        else:
            range_validators.append(_gen_is_valid(range(lb, i+1), width))
            range_validators.append(_gen_is_valid([j], width))

        # Only use a the range validators if its cheaper than enumerating
        if _RANGE_COST * len(range_validators) < len(opcodes):
            def is_valid(opcode: AbstractBitVector) -> AbstractBit:
                return ft.reduce(
                        operator.or_,
                        (f(opcode) for f in range_validators),
                        opcode.get_family().Bit(1))

    return _validator_cache.setdefault(opcodes, is_valid)
