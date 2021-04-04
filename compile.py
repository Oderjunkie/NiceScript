#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
from iteration_utilities import deepflatten
from parsimonious import Grammar, NodeVisitor
import parsimonious.nodes as pNodes

grammar = Grammar(r"""
module = ( NEWLINE? ((statement / COMMENT) (NEWLINE (statement / COMMENT))* NEWLINE?)? )

vardef = ( IDENTIFIER WHITESPACE? EQU WHITESPACE? expr )
       / ( IDENTIFIER WHITESPACE? SEMANTIC_EQU WHITESPACE? expr )
functioncall = IDENTIFIER (WHITESPACE expr)*
ifstat = "if" WHITESPACE (cond / expr)
statement = INDENT* (vardef / ifstat / functioncall)

INDENT = ~" {4}"
EQU = "="
PLUS = "+"
MINUS = "-"
TIMES = "*"
ON = "/"
MOD = "%"
SEMANTIC_TIMES = ("times"/"by")
SEMANTIC_ON = ("on"/"over")
SEMANTIC_MOD = ("mod"/"modulo")
SEMANTIC_PLUS = ("plus"/"and"/"with")
SEMANTIC_MINUS = ("minus"/"without")
SEMANTIC_EQU = "is"

value = NUMBER / STRING / IDENTIFIER

cond = ( expr WHITESPACE? EQU WHITESPACE? expr )
     / ( expr WHITESPACE? SEMANTIC_EQU WHITESPACE? expr )

fromloop = ( "from" WHITESPACE expr WHITESPACE "to" WHITESPACE expr )

expr = fromloop
      / ( value WHITESPACE SEMANTIC_TIMES WHITESPACE value )
      / ( value WHITESPACE SEMANTIC_ON WHITESPACE value )
      / ( value WHITESPACE SEMANTIC_MOD WHITESPACE value )
      / ( value WHITESPACE? TIMES WHITESPACE? value )
      / ( value WHITESPACE? ON WHITESPACE? value )
      / ( value WHITESPACE? MOD WHITESPACE? value )
      / ( value WHITESPACE SEMANTIC_PLUS WHITESPACE value )
      / ( value WHITESPACE SEMANTIC_MINUS WHITESPACE value )
      / ( value WHITESPACE? PLUS WHITESPACE? value )
      / ( value WHITESPACE? MINUS WHITESPACE? value )
      / ( value )

STRING = ~"(\".*?\")|('.*?\')|(`.*?`)"s
NUMBER = (~"[0-9]+") / (~"0x([0-9A-F]|[0-9a-f])*")
IDENTIFIER = ~"[a-zA-Z_$#][-a-zA-Z0-9_$#]*"
NEWLINE = ~"(\r|\n|\r\n)+"
WHITESPACE = ~"[ \t]+"
COMMENT = INDENT* ~"\/\*.*?\*\/"s
""")

def perform_actions(ns):
    global ast
    ast = grammar.parse(ns.replace('\t', '    '))
    class Module:
        def __init__(self, body):
            self.body = deepflatten(body[1][0])
            self.body = [x for x in self.body if x]
        def __repr__(self):
            return 'Module({})'.format(repr(self.body))
        def __str__(self):
            return '\n'.join([str(x) for x in self.body])
    class VarDef:
        def __init__(self, indent=0, set_var=None, to_var=None):
            self.indent = indent
            self.set = set_var
            self.to = to_var
        def __repr__(self):
            return 'Vardef({}, {}, {})'.format(repr(self.indent), repr(self.set), repr(self.to))
        def __str__(self):
            return '    '*self.indent+'{} = {}'.format(self.set, self.to)
    class IfStat:
        def __init__(self, indent=0, left=None, op=None, right=None):
            self.indent = indent
            self.left = left
            self.op = op
            self.right = right
        def __repr__(self):
            return 'IfStat({}, {}, {}, {})'.format(repr(self.indent), repr(self.left), repr(self.op.text), repr(self.right))
        def __str__(self):
            return '    '*self.indent+'if {} {} {}'.format(str(self.left), self.op.text, str(self.right))
    class Name:
        def __init__(self, name):
            self.name = name
        @property
        def text(self):
            return str(self)
        def __repr__(self):
            return 'Name({})'.format(repr(self.name))
        def __str__(self):
            return self.name
    class FuncCall:
        def __init__(self, indent=0, name=None, args=[]):
            self.indent = indent
            self.name = name
            self.args = args
        def __repr__(self):
            return 'FuncCall({}, {}, {})'.format(repr(self.indent), repr(self.name), repr(self.args))
        def __str__(self):
            return '    '*self.indent+'{} {}'.format(str(self.name), ' '.join([str(x) for x in self.args]))
    class FromLoop:
        def __init__(self, _from=None, _to=None):
            self._from = _from
            self._to = _to
        @property
        def text(self):
            return str(self)
        def __repr__(self):
            return 'FromLoop({}, {})'.format(repr(self._from), repr(self._to))
        def __str__(self):
            return 'from {} to {}'.format(str(self._from), str(self._to))
    class Expr:
        def __init__(self, left, op=None, right=None):
            self.left = left
            self.op = op
            self.right = right
        @property
        def text(self):
            return str(self)
        def __repr__(self):
            left = repr(self.left.text)
            if type(self.left)==Name:
                left = repr(self.left)
            if self.op:
                right = repr(self.right.text)
                if type(self.right)==Name:
                    right = repr(self.right)
                return 'Expr({}, {}, {})'.format(left, repr(self.op.text), right)
            return 'Expr({})'.format(left)
        def __str__(self):
            if self.op:
                return '{} {} {}'.format(self.left.text, self.op.text, self.right.text)
            return '{}'.format(self.left.text)
    class DummyNode:
        def __init__(self, children):
            self.children = children
        @property
        def text(self):
            return str(self)
        def __repr__(self):
            return 'DummyNode({})'.format(repr(self.children))
        def __str__(self):
            return ''.join([x.text for x in self.children])
    class TrickOrTreater(NodeVisitor):
        def visit_module(self, node, visited_children):
            body = []
            for child in visited_children:
                body.append(child)
            return Module(body)
        def visit_COMMENT(self, node, visited_children):
            return None
        def visit_NEWLINE(self, node, visited_children):
            return None
        def visit_statement(self, node, visited_children):
            stat = visited_children[1][0]
            name = node.children[1].children[0].expr_name
            if name=='vardef':
                stat = stat[0]
                var = stat[0].text
                index = 1
                def gettext(thing):
                    try:
                        return thing[index][0].text.strip()
                    except:
                        return thing[index].text.strip()
                while gettext(stat)=='':
                    index += 1
                if stat[index].expr_name=='EQU':
                    assert stat[index].text=='='
                else:
                    assert stat[index].text=='is'
                val = 0
                index += 1
                while gettext(stat)=='':
                    index += 1
                val = stat[index]
                final = VarDef(len(node.children[0].children), var, val)
                return final
            if name=='ifstat':
                assert stat[0].text == 'if'
                index = 0
                def gettext(thing):
                    thing = thing[index]
                    while type(thing)==list:
                        thing = thing[0]
                    return thing.text.strip()
                cond = stat[2][0][0]
                left = cond[index]
                index += 1
                while gettext(cond)=='':
                   index += 1
                while gettext(cond)=='':
                   index += 1
                op = cond[index]
                if op.expr_name=='EQU':
                    assert op.text=='='
                    assert op.text=='is'
                index += 1
                while gettext(cond)=='':
                   index += 1
                right = cond[index]
                final = IfStat(len(node.children[0].children), left, op, right)
                return final
            if name=='functioncall':
                funcname = stat[0].text
                args = []
                for expr in stat[1]:
                    args += [expr[1]]
                final = FuncCall(len(node.children[0].children), funcname, args)
                return final
            return None
        def visit_expr(self, node, visited_children):
            if visited_children==None:
                return node
            expr = visited_children[0]
            try:
                if expr[0].text=='from':
                    expr = DummyNode(visited_children[0])
                    index = 0
                    assert expr.children[index].text == 'from'
                    index += 1
                    while expr.children[index].text.strip()=='':
                        index += 1
                    from_num = self.visit_expr(expr.children[index], None)
                    index += 1
                    while expr.children[index].text.strip()=='':
                        index += 1
                    assert expr.children[index].text == 'to'
                    index += 1
                    while expr.children[index].text.strip()=='':
                        index += 1
                    to_num = self.visit_expr(expr.children[index], None)
                    return FromLoop(from_num, to_num)
            except:
                pass
            if len(expr)==1:
                expr = expr[0]
                try:
                    expr = expr[0]
                except:
                    expr = expr
                if expr.expr_name=='IDENTIFIER':
                    return Expr(Name(expr.text))
                return Expr(expr)
            arr = []
            for part in expr:
                while type(part)==list:
                    part = part[0]
                if part.expr_name!='WHITESPACE':
                    arr += [part]
            if arr[0].expr_name=='IDENTIFIER':
                arr[0] = Name(arr[0].text)
            if len(arr)>1:
                if arr[2].expr_name=='IDENTIFIER':
                    arr[2] = Name(arr[2].text)
            return Expr(*arr)
        def generic_visit(self, node, visited_children):
            return visited_children or node
    def reparse(tree, indent=0):
        newtree = TrickOrTreater().visit(tree)
        return newtree
    def javascript(module):
        global inline
        scope = []
        inline = False
        def expr2js(expr):
            if type(expr.left)==Name and expr.left.name not in scope:
                    scope.append(expr.left.name)
            if expr.op:
                op = expr.op.text
                if op in ['+', 'plus', 'and', 'with']:
                    op = '+'
                elif op in ['-', 'minus', 'without']:
                    op = '-'
                elif op in ['*', 'times', 'by']:
                    op = '*'
                elif op in ['/', 'on', 'over']:
                    op = '/'
                elif op in ['%', 'mod']:
                    op = '%'
                if type(expr.right)==Name and expr.right.name not in scope:
                    scope.append(expr.right.name)
                left = expr.left
                right = expr.right
                if type(left)==Name:
                    left = left.name
                else:
                    try:
                        if left.expr_name=='STRING':
                            left = left.text
                        else:
                            left = int(left)
                    except:
                        left = int(left)
                if type(right)==Name:
                    right = right.name
                else:
                    try:
                        if right.expr_name=='STRING':
                            right = right.text
                        else:
                            right = int(right.text)
                    except:
                        right = right.text
                return '{} {} {}'.format(left, op, right)
            else:
                if type(expr.left)==Name:
                    return expr.left.name
                else:
                    try:
                        if expr.left.expr_name=='STRING':
                            return expr.left.text
                        else:
                            return int(expr.left.text)
                    except:
                        return int(expr.left.text)
        def vardef2js(vardef):
            global inline
            if vardef.set not in scope:
                    scope.append(vardef.set)
            if type(vardef.to)==FromLoop:
                inline = True
                return 'for ({0} = {1}; {0} < {2}+1; {0}++) '.format(vardef.set, vardef.to._from, vardef.to._to)
            else:
                return '{} = {};\n'.format(vardef.set, expr2js(vardef.to))
        def if2js(ifstat):
            global inline
            inline = True
            if ifstat.op:
                return 'if ({} == {}) '.format(expr2js(ifstat.left), expr2js(ifstat.right))
            else:
                return 'if ({}) '.format(expr2js(ifstat.left))
        def func2js(funccall):
            name = funccall.name
            if funccall.name not in scope:
                scope.append(funccall.name)
            if name=='print':
                name = 'console.log'
            if name=='skip':
                return 'continue;\n'
            if name=='break':
                return 'break;\n'
            return '{}({});\n'.format(name, ', '.join([expr2js(x) for x in funccall.args]))
        lastindent = 0
        code = ''
        for stmt in module.body:
            if stmt.indent!=lastindent:
                if abs(stmt.indent-lastindent)>1:
                    raise SyntaxError('uhhhh')
                if stmt.indent>lastindent:
                    if inline:
                        inline = False
                        code += '{\n'
                    else:
                        code += '    '*stmt.indent+'{\n'
                else:
                    if inline:
                        inline = False
                        code += '}\n'
                    else:
                        code += '    '*stmt.indent+'}\n'
                lastindent = stmt.indent
            if type(stmt)==VarDef:
                code += '    '*stmt.indent+vardef2js(stmt)
            elif type(stmt)==IfStat:
                code += '    '*stmt.indent+if2js(stmt)
            elif type(stmt)==FuncCall:
                code += '    '*stmt.indent+func2js(stmt)
        if lastindent!=0:
                if lastindent>1:
                    raise SyntaxError('uhhhh')
                code += '}\n'
        if len(scope)>0:
            code = 'var '+', '.join(scope)+';\n'+code
        return code
    ast = reparse(ast)
    return javascript(ast)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='in_file', type=str,
                        help='The input nicescript file')
    parser.add_argument('-o', type=str, default='a.out',
                        help='The output file. (defaults to a.out)')
    args = parser.parse_args()
    with open(args.o, 'w') as fout:
        with open(args.input, 'r') as fin:
            fout.write(perform_actions(fin.read()))
            fin.close()
        fout.close()
