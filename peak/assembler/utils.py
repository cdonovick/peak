import ast
import astor
import logging
import tempfile
import os
import magma as m
import traceback


class ISABuilderAssembler(ast.NodeTransformer):
    def __init__(self, assemblers, _locals, _globals):
        self.assemblers = assemblers
        self._locals = _locals
        self._globals = _globals

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Load):
            try:
                value = eval(compile(ast.Expression(node.value),
                                     filename="<ast>", mode="eval"),
                             self._locals, self._globals)
                if value in self.assemblers:
                    node_val = eval(compile(ast.Expression(node),
                                            filename="<ast>", mode="eval"),
                                    self._locals, self._globals)
                    bv_type, assembler = self.assemblers[value]
                    return ast.Num(int(assembler(getattr(bv_type, node.attr))))
            except NameError:
                pass
        return node


def assemble_values_in_func(assemblers, peak_fn, _locals, _globals):
    func_def = m.ast_utils.get_ast(peak_fn).body[0]
    func_def = ISABuilderAssembler(assemblers, _locals, _globals).visit(func_def)
    func_def = ast.fix_missing_locations(func_def)
    temp_dir = tempfile.mkdtemp()
    file_name = os.path.join(temp_dir, peak_fn.__name__ + ".py")
    with open(file_name, "w") as fp:
        fp.write(astor.to_source(func_def))
    try:
        exec(compile(ast.Module([func_def]), filename=file_name, mode="exec"),
             _globals, _locals)
    except:
        tb = traceback.format_exc()
        logging.error(tb)
        raise Exception(f"Error occured when compiling and executing assemble_values_in_func on function {peak_fn.__name__}, see above") from None
    return _locals[peak_fn.__name__]
