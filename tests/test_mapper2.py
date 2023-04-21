import random
import hwtypes as ht
from itertools import count
from hwtypes.adt_util import ADTVisitor
_id = count()
def get_id():
    return next(_id)

def rand_bool():
    return bool(random.randint(0,1))

def gen_random_adt(d_range, b_range, depth=0):
    if depth == d_range.stop:
        b = random.randrange(b_range.start, b_range.stop)
        if rand_bool():
            T = ht.BitVector[b]
        else:
            T = ht.Enum.from_fields(
                f'E{get_id()}',
                {f'val_{i}' : v for i,v in enumerate(range(b))}
            )
    else:
        num_fields = random.randrange(b_range.start, b_range.stop)
        if num_fields <= 0 and depth >= d_range.start:
            T = gen_random_adt(range(depth, depth), b_range, depth)
        elif rand_bool():
            T = ht.Product.from_fields(
                f'P{get_id()}',
                {
                    f'field_{i}' : gen_random_adt(d_range, b_range, depth+1)
                    for i in range(num_fields)
                }
            )
        else:
            T = ht.Sum[(gen_random_adt(d_range, b_range, depth+1) for _ in range(num_fields))]
    return T


class ADTPrinter(ADTVisitor):
    def __init__(self, tabwidth=4):
        self.d = 0
        self.tab = ' '*tabwidth

    def _print_class_head(self, adt_t, base=None):
        s = 'class ' + str(adt_t)
        if base:
            s += f'({base})'
        s += ':'
        self._print_tab()
        print(s)

    def _print_tab(self, offset=0):
        print(self.tab * (self.d + offset), end='')

    def visit_leaf(self, adt_t):
        self._print_tab()
        print(str(adt_t))

    def visit_Enum(self, adt_t):
        self._print_class_head(adt_t, 'Enum')
        for k,v in adt_t.field_dict.items():
            self._print_tab(1)
            print(k + ' = ' + str(v._value_))

    def visit_Product(self, adt_t):
        self._print_class_head(adt_t, 'Product')
        for k,v in adt_t.field_dict.items():
            self._print_tab(1)
            print(k + ' = (')
            self.d += 2
            self.visit(v)
            self.d -= 2
            self._print_tab(1)
            print(')')

    def visit_Sum(self, adt_t):
        self._print_tab()
        print('Sum [')
        self.d += 1
        for k,v in adt_t.field_dict.items():
            self.visit(v)
            self._print_tab()
            print(',')
        self.d -= 1
        self._print_tab()
        print(']')
