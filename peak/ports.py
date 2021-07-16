
import typing as tp
from enum import Enum as pyEnum, auto
from hwtypes.adt_meta import BoundMeta

class Direction(pyEnum):
    IN = auto()
    OUT = auto()


class PortMeta(BoundMeta):
    def __getitem__(cls, idx: tp.Type) -> 'PortMeta':
        if isinstance(idx, tuple):
            raise TypeError(f'expected a single type not {idx}')
        return super().__getitem__(idx)

    @property
    def bound_t(cls) -> tp.Type:
        return cls.fields[0]


class Port(metaclass=PortMeta):
    def __init__(self, direction: Direction, owner: tp.Any, name: str):
        self.direction = direction
        self.owner = owner
        self.name = name

    def __repr__(self):
        return f'{self.owner}.{self.name} :: {type(self).bound_t}({self.direction})'

    def _clone(self, owner):
        return type(self)(self.direction, owner, self.name)

    def __imatmul__(self, other):
        if self.direction is not Direction.IN:
            raise TypeError(f'cannot wire to output port {self.name}')

        if not isinstance(other, type(self).bound_t):
            raise TypeError(f'expect value of type {type(self).bound_t} not {type(other)}')

        self.owner._inputs_[self.name] = other
        return self
