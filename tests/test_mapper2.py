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
        choice = random.randrange(0,4)
        match choice:
            case 0:
                T = ht.Product.from_fields(
                    f'P{get_id()}',
                    {
                        f'field_{i}' : gen_random_adt(d_range, b_range, depth+1)
                        for i in range(num_fields)
                    }
                )
            case 1:
                T = ht.Tuple[(gen_random_adt(d_range, b_range, depth+1) for _ in range(num_fields))]
            case 2:
                T = ht.TaggedUnion.from_fields(
                    f'U{get_id()}',
                    {
                        f'field_{i}' : gen_random_adt(d_range, b_range, depth+1)
                        for i in range(num_fields)
                    }
                )
            case 3:
                T = ht.Sum[(gen_random_adt(d_range, b_range, depth+1) for _ in range(num_fields))]

    return T

class RandomVisitor(ADTVisitor):
    def __init__(self):
        self._children = []

    def visit_leaf(self, adt_t):
        if issubclass(adt_t, ht.Bit):
            val = random.choice([False, True])
        elif issubclass(adt_t, ht.BitVector):
            val = random.randrange(1 << adt_t.size)
        else:
            raise TypeError()

        self._children.append(adt_t(val))

    def visit_Enum(self, adt_t):
        val = random.choice(adt_t.fields)
        self._children.append(val)

    def visit_Product(self, adt_t):
        self.generic_visit(adt_t)
        n = len(adt_t.field_dict)
        children = self._children[-n:]
        self._children[-n:] = [adt_t(*children)]

    def visit_Tuple(self, adt_t):
        self.generic_visit(adt_t)
        n = len(adt_t.field_dict)
        children = self._children[-n:]
        self._children[-n:] = [adt_t(*children)]

    def visit_TaggedUnion(self, adt_t):
        self.generic_visit(adt_t)
        n = len(adt_t.field_dict)
        children = self._children[-n:]
        choice = random.randrange(n)
        key = list(adt_t.field_dict.keys())[choice]
        val = children[choice]
        assert isinstance(val, adt_t.field_dict[key])
        self._children[-n:] = [adt_t(**{key:val})]

    def visit_Sum(self, adt_t):
        self.generic_visit(adt_t)
        n = len(adt_t.field_dict)
        children = self._children[-n:]
        choice = random.randrange(n)
        key = list(adt_t.field_dict.keys())[choice]
        val = children[choice]
        assert isinstance(val, adt_t.field_dict[key])
        self._children[-n:] = [adt_t(val)]


def gen_random_instance(adt_t):
    v = RandomVisitor()
    v.visit(adt_t)
    assert len(v._children) == 1
    return v._children[0]

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

    def visit_Tuple(self, adt_t):
        self._print_tab()
        print('Tuple [')
        self.d += 1
        for k,v in adt_t.field_dict.items():
            self.visit(v)
            self._print_tab()
            print(',')
        self.d -= 1
        self._print_tab()
        print(']')

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

    def visit_TaggedUnion(self, adt_t):
        self._print_class_head(adt_t, 'TaggedUnion')
        for k,v in adt_t.field_dict.items():
            self._print_tab(1)
            print(k + ' = (')
            self.d += 2
            self.visit(v)
            self.d -= 2
            self._print_tab(1)
            print(')')
