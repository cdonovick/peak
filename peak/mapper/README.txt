The code that does the automatic mapping is rather complicated. This document is an attempt to define necessary terms in order to understand the codebase.

Before describing how to create the single SMT formula, the following terms need to be defined:

----------------ADT---------------
This is an Algebraic Data Type that can be any of the following:
  Product
  Tuple
  Sum
  Enum
  Bit/Bitvector

It is important to think of an ADT type as a Tree data structure. Product/Tuple and Sum all contain some number of child ADT types whereas Enum/Bit/Bitvector are all the leaf nodes of the ADT tree 

----------------Path---------------
The term 'path' refers to a tuple describing the 'path' to a particular node in the adt tree in terms of product/tuple/sum fields. For example:

class A(Product):
    a=T0
    b=T1
class B(Product):
    a=Sum[A,T2]
    b=T3

Here are the complete list of paths for B (and their corresponding types)
   () -> B
   ('a',) -> Sum[A,T2]
   ('a', A) -> A
   ('a', A, 'a') -> T0
   ('a', A, 'b') -> T1
   ('a', T2) -> T2
   ('b',) -> Bit

----------------Form---------------
Any adt type has an isomorphic adt type which is in 'Sum of Products' form. The word 'Form' refers to one of the 'Products' of this SoP. Forms are uniquely deterined by each Sum decision of the original adt and contains only the leaf nodes from those decisions

For example in the above ADT type B the following 2 forms are:

Form 1:
  sum choices: [('a',) -> A]
  leaf nodes:
     ('a', A, 'a') -> T0
     ('a', A, 'b') -> T1
     ('b',) -> Bit

Form 2:
  sum choices: [('a',) -> T]
  leaf nodes:
     ('a', T2) -> T2
     ('b',) -> Bit

---------------family closure----------------
family closure (often abbreviated as 'fc') is a function that takes in one argument (the family) and returns a Peak class defined in terms of that family. These functions should always be cached.

---------------input_t/output_t--------------
The automatic mapper requires any peak class to annotate the names and types of all inputs and outputs. This is accomplished using the 'name_outputs' decorator on the __call__ method. This gives everyone access to the adt type which represents the input (input_t) and the adt type represenitng the output (output_t).

For example:

class PE(Peak):
   @name_outputs(o1=T3,o2=T4)
   def __call__(self, a=T1,b=T2):
      ...

PE.input_t would be equivelent to:

class Input(Product):
  a=T1
  b=T2

and PE.output_t would be equivelent to:
class Output(Product):
  o1=T3
  o2=T4

----------------ir/arch---------------
The problem of automatic mapping is formulated between an ir primitve and an arch (isa) primitive which are both represented as a family_closure generating a peak class.

Automatic mapping tries to solve the following problem: Given an aribtrary value of type ir.input_t (ir_input), how can you construct a value of type arch.input_t (arch_input) such that ir(ir_input) == arch(arch_input).

Caveat: This is almost, but not quite correct given that the output types of the ir and the arch could be different. 


----------------Binding---------------
A Binding should be thought of as one possible way to match all the leaf nodes of ir.input_t to arch.input_t. More precisely, it is one way to match one form of ir.input_t to one form of arch.input_t

A Binding is represented as a list of path pairs where one path is from the ir and one path is from the arch
It is usually in the form tp.List[Tuple[ir_path, arch_path] with the caveat that 'ir_path' could be 'Unbound' or a constant value
For example
 class IRInput(Product):
     a = Bit
     b = BV[8]
 class ArchInput(Product):
     c = Bit
     d = Bit
     e = BV[8]

 This has two valid bindings
 1:
   ('a',)  <=> ('c',)
   ('b',)  <=> ('e',)
   Unbound <=> ('d',)
 2:
   ('a',)  <=> ('d',)
   ('b',)  <=> ('e',)
   Unbound <=> ('c',)


To be continued...
