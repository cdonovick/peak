from enum import Enum

__all__ = ['Enum', 'is_enum']

def is_enum(t):
    return issubclass(t,Enum)
