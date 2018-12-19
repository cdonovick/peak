from enum import Enum

__all__ = ['Enum', 'is_enum']

def is_enum(enum):
    return isinstance(enum,Enum)
