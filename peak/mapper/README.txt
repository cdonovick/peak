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
  sum choices: [('a',) -> T2]
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
   def __call__(self, a : T1, b : T2):
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
     i = Const(BV[4]) #This represent the instruction

Note that that ArchInput.i is labeled as a constant type. This indicates a compile-time constant like an instruction op code or an immediate value

 This has two valid bindings
 1:
   ('a',)  <=> ('c',)
   ('b',)  <=> ('e',)
   Unbound(Bit) <=> ('d',)
   Constant(BV[4]) <=> ('i',)
 2:
   ('a',)  <=> ('d',)
   ('b',)  <=> ('e',)
   Unbound(Bit) <=> ('c',)
   Constant(BV[4]) <=> ('i',)


Another way to think of a Binding is as a function from ArchInput to IRInput. This is the appropriate directionality 
as IR must always be able to be constructed from the Arch, but the other way around might not be true
For example in this case, the function for input binding 1 would be:

def InputBinding1(ai : ArchInput) -> IRInput:
  return IRInput(a=ai.c, b=ai.e)


----------------Finding Rewrite Rules---------------

Given a function IR :: IRInput -> IROutput
and a function Arch :: ArchInput -> ArchOutput,

The goal is to solve the following problem:

Find InputBinding, OutputBinding, and any Constant values in the bindings
  ST ForALL archIn : ArchInput,
    let irIn = InputBinding(archIn)
    let irOut = IR(irIn)
    let archOut = Arch(archIn)
    assert OutputBinding(archOut) == irOut


The following is a more concrete (yet still simple) example of how to explicitly construct the SMT formula

Given the functions 
IR :: IRInput -> IROutput
Arch :: ArchInput -> ArchOutput
with the following Types

class IRInput(Product):
     a = Bit
     b = BV[8]

class ArchInput(Product):
     c = Bit
     d = Bit
     e = BV[8]
     i = Const(BV[4]) #This represent the instruction

IROutput = ArchOutput = Tuple[BV[8]]

This would produce the following possible input bindings:
 1:
   ('a',)  <=> ('c',)
   ('b',)  <=> ('e',)
   Unbound(Bit) <=> ('d',)
   Constant(BV[4]) <=> ('i',)
 2:
   ('a',)  <=> ('d',)
   ('b',)  <=> ('e',)
   Unbound(Bit) <=> ('c',)
   Constant(BV[4]) <=> ('i',)

Along with the corresponding functions 
  InputBinding1 :: ArchInput -> IRInput
  InputBinding2 :: ArchInput -> IRInput

And a single Output Binding:
 1:
    (0,) <=> (0,)

Along with the single function
  OutputBinding1 :: ArchOutput -> IROutput


We start by creating a unique Free Variable for each leaf node of the ArchInput type
('c',) : C = SMTBit()
('d',) : D = SMTBit()
('e',) : E = SMTBitVector[8]()
('i',) : I = SMTBitVector[4]()

along with a Free variable to choose which inputbinding it is 
  Bi = SMTBitVector[2]()
and which outputbinding it is
  Bo = SMTBitVector[1]()


We then construct the formula in the following way:
let archIn = ArchInput(c=C,d=D,e=E,i=I)
let archOut = Arch(archIn)
let irIn1 = InputBinding1(archIn)
let irOut1 = IR(irIn1)
let irIn2 = InputBinding2(archIn)
let irOut2 = IR(irIn2)
Exists(I, B) such that ForAll(C, D, E)
    ( (Bi==1) & (Bo==1) & (irOut1 == OutputBinding1(archOut)) ) 
  | ( (Bi==2) & (Bo==1) & (irOut2 == OutputBinding1(archOut)) )


If there were 4 input bindings and 2 output bindings, the number of ORed terms would be 4*2 == 8

Unfortunately, this is still not the full story. If any Input or Output type has more than one Form (defined earlier), 
each Product in the final Sum of Products gets more terms identifying which form it belongs to.

TODO define above statment more explicitly
