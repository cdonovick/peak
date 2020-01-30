import magma
from hwtypes import Enum, Product, Tuple

def Enum_fc(family):
    if family is magma.get_family():
        return magma.Enum
    else:
        return Enum

def Product_fc(family):
    if family is magma.get_family():
        return magma.Product
    else:
        return Product

def Tuple_fc(family):
    if family is magma.get_family():
        return magma.Tuple
    else:
        return Tuple

