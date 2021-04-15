#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
from iteration_utilities import deepflatten
from parsimonious import Grammar, NodeVisitor
import parsimonious.nodes as pNodes
import sys

def reccursive_debug_list(arg):
    if type(arg)==list:
        out = [reccursive_debug_list(el) for el in arg]
        out = '[' + ', '.join(out) + ']'
        return out
    return str(arg)

def traceback(e):
    print('Custom traceback:')
    print('File "{}", line {}, in {}'.format(e.__traceback__.tb_frame.f_code.co_filename, e.__traceback__.tb_frame.f_code.co_firstlineno, e.__traceback__.tb_frame.f_code.co_name))
    with open(e.__traceback__.tb_frame.f_code.co_filename) as f:
        lines = f.readlines()
        line = e.__traceback__.tb_lineno-1
        print('    {}\t{}'.format(line-1, lines[line-1][:-1]))
        print('>>> {}\t{}'.format(line,   lines[line][:-1]))
        print('    {}\t{}'.format(line+1, lines[line+1][:-1]))
        print('{}: {}'.format(str(type(e))[8:-2], str(e)))
        f.close()
        sys.exit()

grammar = Grammar(r"""
module = ( NEWLINE? ((COMMENT / statement) (NEWLINE (COMMENT / statement))* NEWLINE?)? )

statement = INDENT* expr_func

INDENT = ~" {4}"
EQU = "="/"is"
NOTEQU = "!="/"is not"
GT = ">"/"is more than"
GTE = ">="
LT = "<"/"is less than"
LTE = "<="
PLUS = "+"
MINUS = "-"
TIMES = "*"
ON = "/"
MOD = "%"
SEM_PLUS = ("plus")
SEM_MINUS = ("minus")
SEM_TIMES = ("times"/"by")
SEM_ON = ("over")
SEM_MOD = ("mod"/"modulo")
DOT = "."
comparison = LTE / GTE / LT / GT / NOTEQU / EQU
value = ('(' WHITESPACE? expr_func WHITESPACE? ')') / array / object / NUMBER / STRING / REGEX / function / 'undefined' / 'null' / IDENTIFIER

cond = ( ( value ) WHITESPACE? comparison WHITESPACE? ( value ) )

algebraic_op = PLUS/MINUS/TIMES/ON/MOD/DOT
semantic_op = SEM_PLUS/SEM_MINUS/SEM_TIMES/SEM_ON/SEM_MOD

fromloop = ( "from" WHITESPACE expr WHITESPACE "to" WHITESPACE expr )
vardef = ( IDENTIFIER WHITESPACE? EQU WHITESPACE? expr_func )
functioncall = value (WHITESPACE expr)+
ifstat = "if" WHITESPACE (cond)
elsestat = "else"
function = IDENTIFIER? (WHITESPACE IDENTIFIER)* WHITESPACE? '->' WHITESPACE? expr_func?

expr_func = vardef
          / function
          / ( value WHITESPACE? algebraic_op WHITESPACE? value )
          / ( value WHITESPACE semantic_op WHITESPACE value )
          / ( value '[' WHITESPACE? value WHITESPACE? ']' )
          / fromloop
          / ifstat
          / elsestat
          / functioncall
          / ( value )

expr = vardef
     / function
     / ( value WHITESPACE algebraic_op WHITESPACE value )
     / ( value '[' WHITESPACE? value WHITESPACE? ']' )
     / fromloop
     / ifstat
     / elsestat
     / ( value )

array = '[' ((WHITELINE? value WHITELINE? ',')* (WHITELINE? value))? WHITELINE? ']'
object = '{' ((WHITELINE? value WHITELINE? ':' WHITELINE? value WHITELINE? ',')* (WHITELINE? value WHITELINE? ':' WHITELINE? value))? WHITELINE? '}'
STRING = ~"(\".*?\")|('.*?\')|(`.*?`)"s
NUMBER = (~"[0-9]+") / (~"0x([0-9A-F]|[0-9a-f])*")
REGEX = ~"\/([^\/]|\\\/)*?\/"
IDENTIFIER = ~"[a-zA-Z_$#][a-zA-Z0-9_$#]*"
NEWLINE = ~"(\r|\n|\r\n)+"
WHITESPACE = ~"[ \t]+"
WHITELINE = ~"(\r|\n|\r\n|[ \t])+"
COMMENT = INDENT* ~"(\/\*.*?\*\/)|(\/\/.*\n)"s
""")

parse = None

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
        def __init__(self, set_var=None, to_val=None):
            self.set = set_var
            self.to = to_val
        def __repr__(self):
            return 'Vardef({}, {})'.format(repr(self.set), repr(self.to))
        def __str__(self):
            return '{} = {}'.format(self.set, self.to)
    class IfStat:
        def __init__(self, term):
            self.term = term
        def __repr__(self):
            return 'IfStat({})'.format(repr(self.term))
        def __str__(self):
            return 'if {}'.format(str(self.term))
    class ElseStat:
        def __init__(self):
            pass
        def __repr__(self):
            return 'ElseStat()'
        def __str__(self):
            return 'else'
    class Stat:
        def __init__(self, indent=0, expr=None):
            self.indent = indent
            self.expr = expr
        @property
        def text(self):
            return str(self)
        def __repr__(self):
            return 'Stat({}, {})'.format(repr(self.indent), repr(self.expr))
        def __str__(self):
            return '    '*self.indent+str(self.expr)
    class Name:
        def __init__(self, name=''):
            self.name = name
        @property
        def text(self):
            return str(self)
        def __repr__(self):
            return 'Name({})'.format(repr(self.name))
        def __str__(self):
            return self.name
    class FuncCall:
        def __init__(self, name=None, args=[]):
            self.name = name
            self.args = []
            for arg in args:
                if type(arg)==list and len(arg)==1:
                    self.args.append(arg[0])
                    continue
                self.args.append(arg)
        @property
        def text(self):
            return str(self)
        @property
        def expr_name(self):
            return 'functioncall'
        def __repr__(self):
            return 'FuncCall({}, {})'.format(repr(self.name), repr(self.args))
        def __str__(self):
            return '{} {}'.format(str(self.name), ' '.join([str(x) for x in self.args]))
    class Lambda:
        def __init__(self, args=[], result=None):
            self.args = args
            self.result = result
        @property
        def text(self):
            return str(self)
        @property
        def expr_name(self):
            return 'function'
        def __repr__(self):
            return 'Lambda({}, {})'.format(repr(self.args), repr(self.result))
        def __str__(self):
            return '{} -> {}'.format(' '.join([str(x) for x in self.args]), str(self.result))
    class FromLoop:
        def __init__(self, from_=None, to_=None):
            self.from_ = from_
            self.to_ = to_
        @property
        def text(self):
            return str(self)
        def __repr__(self):
            return 'FromLoop({}, {})'.format(repr(self.from_), repr(self.to_))
        def __str__(self):
            return 'from {} to {}'.format(str(self.from_), str(self.to_))
    class Cond:
        def __init__(self, left, comp, right):
            self.left = left
            self.comp = comp
            self.right = right
        @property
        def text(self):
            return str(self)
        def __repr__(self):
            return 'Cond({}, {}, {})'.format(repr(self.left), repr(self.comp), repr(self.right))
        def __str__(self):
            return '{} {} {}'.format(str(self.left), str(self.comp), str(self.right))
    class Regex():
        def __init__(self, string):
            self.string = string
        def __str__(self):
            return self.string
        def __repr__(self):
            return 'Regex({})'.format(self.string)
    class Array():
        def __init__(self, arr):
            self.arr = arr
        def __str__(self):
            return str(self.arr)
        def __repr__(self):
            return 'Array(' + reccursive_debug_list(self.arr) + ')'
        def __iter__(self):
            return iter(self.arr)
    class Object():
        def __init__(self, arr):
            self.arr = arr
        def __str__(self):
            out = '{'
            for k,v in self.arr:
                out += '{}: {}'.format(str(k), str(v))
            out += '}'
            return out
        def __repr__(self):
            return 'Object(' + reccursive_debug_list(self.arr) + ')'
        def __iter__(self):
            return iter(self.arr)
    class Expr:
        def __init__(self, left, op=None, right=None):
            self.left = left
            self.op = op
            self.right = right
        @property
        def text(self):
            return str(self)
        def __repr__(self):
            left = repr(self.left)
            if self.op:
                right = repr(self.right)
                return 'Expr({}, {}, {})'.format(left, repr(self.op), right)
            return 'Expr({})'.format(left)
        def __str__(self):
            left = self.left
            try:
                left = left.text
            except Exception:
                pass
            if self.op:
                op = self.op
                try:
                    op = op.text
                except Exception:
                    pass
                right = self.right
                try:
                    right = right.text
                except Exception:
                    pass
                return '{} {} {}'.format(left, op, right)
            return '{}'.format(left)
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
            yo = visited_children or node
            try:
                if type(yo[0])!=pNodes.Node:
                    return Stat(len(yo[0]), yo[1][0])
                else:
                    return Stat(0, yo[1][0])
            except Exception as e:
                try:
                    if type(yo[0])!=pNodes.Node:
                        return Stat(len(yo[0]), yo[1])
                    else:
                        return Stat(0, yo[1])
                except Exception as e2:
                    print('Stat error: {}, {}'.format(e, e2))
                    return yo
        def visit_vardef(self, node, visited_children):
            try:
                final = []
                for part in visited_children:
                    while type(part)==list:
                        part = part[0]
                    try:
                        if part.text.strip()=='':
                            continue
                    except Exception as e:
                        print('Vardef value parsing error: {}'.format(e))
                        if str(part).strip()=='':
                            continue
                    final.append(part)
                return VarDef(Name(final[0].text), final[-1])
            except Exception as e:
                print('VarDef error: {}'.format(e))
                traceback(e)
                return visited_children or node
        def visit_function(self, node, visited_children):
            args = []
            expr = None
            try:
                for child in visited_children:
                    while type(child)==list:
                        child = child[-1]
                    if child.text.strip()=='':
                        continue
                    try:
                        if child.expr_name=='IDENTIFIER':
                            args.append(Name(child.text))
                            continue
                    except Exception:
                        pass
                    if child.text=='->':
                        continue
                    expr = child
                return Lambda(args, expr)
            except Exception as e:
                print('Function error: {}'.format(e))
                return visited_children or node.children
        def visit_functioncall(self, node, visited_children):
            try:
                part = visited_children[1]
                args = [x[1] for x in part]
                final = None
                if type(visited_children[0]) not in [Expr, Name]:
                    if visited_children[0].expr_name=='IDENTIFIER':
                        final = FuncCall(Name(visited_children[0].text), args)
                    else:
                        raise Exception('we dont support that many function call things k thx bye')
                else:
                    final = FuncCall(visited_children[0], args)
                return final
            except Exception as e:
                print('FunctionCall error: {}'.format(e))
                traceback(e)
                return visited_children or node
        def visit_fromloop(self, node, visited_children):
            finals = []
            try:
                for part in visited_children:
                    while type(part)==list:
                        part = part[0]
                    try:
                        if part.text.strip()=='':
                            continue
                    except Exception:
                        pass
                    finals.append(part)
                assert finals[0].text=='from'
                assert finals[2].text=='to'
                return FromLoop(finals[1], finals[3])
            except Exception as e:
                print('FromLoop error: {}'.format(e))
                return visited_children or node
        def visit_expr(self, node, visited_children):
            thing = visited_children or node
            try:
                if type(thing[0])==Name:
                    return thing[0]
                if type(thing[0])==Lambda:
                    return thing[0]
                if type(thing[0])==pNodes.RegexNode:
                    return thing[0].text
                if type(thing[0])!=list:
                    return thing
                thing = thing[0]
                if len(thing)==1:
                    if thing[0].expr_name=='IDENTIFIER':
                        return Name(thing[0].text)
                    if thing[0].expr_name=='STRING':
                        return thing[0].text
                    if thing[0].expr_name=='REGEX':
                        return Regex(thing[0].text)
                    if type(thing[0])==Lambda:
                        return thing[0]
                finals = []
                for parts in thing:
                    while True:
                        if type(parts)!=list:
                            parts = [parts]
                            break
                        if len(parts)>1:
                            break
                        parts = parts[0]
                    cleaned = []
                    try:
                        for part in parts:
                            try:
                                if part.expr_name=='WHITESPACE':
                                    continue
                            except Exception:
                                pass
                            cleaned.append(part)
                    except Exception:
                        pass
                    if cleaned:
                        try:
                            finals.append(cleaned[0])
                        except Exception:
                            pass
                return Expr(finals[0], finals[1].text, finals[2])
            except Exception as e:
                print('Expr error: {}'.format(e))
                return visited_children or node
        def visit_expr_func(self, node, visited_children):
            thing = visited_children or node
            finals = []
            try:
                if type(thing[0])==Name:
                    return thing[0]
                if type(thing[0])==Lambda:
                    return thing[0]
                if type(thing[0])==pNodes.RegexNode:
                    return thing[0].text
                if type(thing[0])!=list:
                    return thing
                thing = thing[0]
                try:
                    if len(thing)==1:
                        if thing[0].expr_name=='IDENTIFIER':
                            return Name(thing[0].text)
                        if thing[0].expr_name=='STRING':
                            return thing[0].text
                        if thing[0].expr_name=='REGEX':
                            return Regex(thing[0].text)
                        if type(thing[0])==Lambda:
                            return thing[0]
                except Exception:
                    pass
                finals = []
                for parts in thing:
                    while True:
                        if type(parts)!=list:
                            parts = [parts]
                            break
                        if len(parts)>1:
                            break
                        parts = parts[0]
                    cleaned = []
                    try:
                        for part in parts:
                            try:
                                if part.expr_name=='WHITESPACE':
                                    continue
                            except Exception:
                                pass
                            cleaned.append(part)
                    except Exception:
                        pass
                    if cleaned:
                        try:
                            finals.append(cleaned[0])
                        except Exception:
                            pass
                return Expr(finals[0], finals[1].text, finals[2])
            except Exception as e:
                return finals[0]
        def visit_cond(self, node, visited_children):
            part = visited_children or node
            left = part[0]
            comp = part[2][0][0].text
            right = part[4]
            if type(left) in [int, float]:
                left = Expr(left)
            if type(right) in [int, float]:
                right = Expr(right)
            return Cond(left, comp, right)
        def visit_ifstat(self, node, visited_children):
            part = visited_children or node
            condexpr = part[2]
            while type(condexpr)==list:
                condexpr = condexpr[0]
            return IfStat(condexpr)
        def visit_value(self, node, visited_children):
            text = visited_children
            try:
                itr = 0
                while type(text)==list:
                    itr += 1
                    text = text[len(text)//2]
                if type(text) in [Expr, FuncCall, Lambda, FromLoop, Array, Object]:
                    return text
                if text.expr_name=='IDENTIFIER':
                    return Name(text.text)
                if text.expr_name=='STRING':
                    return text.text[1:-1]
                if text.expr_name=='REGEX':
                    return Regex(text.text)
                num = float(text.text)
                if int(num)==num:
                    num = int(num)
                return num
            except Exception as e:
                print('Value error: {}'.format(e))
                return visited_children or node
        def visit_array(self, node, visited_children):
            part = visited_children or node
            assert part[0].text=='['
            assert part[3].text==']'
            if type(part[1])!=list:
                return Array([])
            arrayret = [None]*(len(part[1][0][0])+1) # prevent reallocs
            try:
                for i, el in enumerate(part[1][0][0]):
                    assert el[3].text==','
                    arrayret[i] = el[1]
                arrayret[-1] = part[1][0][1][1]
                return Array(arrayret)
            except Exception as e:
                traceback(e)
            return part
        def visit_object(self, node, visited_children):
            part = visited_children or node
            assert part[0].text=='{'
            assert part[3].text=='}'
            if type(part[1])!=list:
                return Object([])
            arrayret = [[None, None]]*(len(part[1][0][0].children)+1) # prevent reallocs
            try:
                for i, el in enumerate(part[1][0][0]):
                    assert el[3].text==':'
                    assert el[7].text==','
                    arrayret[i][0] = el[1]
                    arrayret[i][1] = el[5]
                arrayret[-1] = part[1][0][1][1]
                return Object(arrayret)
            except Exception as e:
                traceback(e)
            return part
        def visit_elsestat(self, node, visited_children):
            return ElseStat()
        def generic_visit(self, node, visited_children):
            return visited_children or node
    def reparse(tree):
        newtree = TrickOrTreater().visit(tree)
        return newtree
    def javascript(module):
        global block
        global scope
        scope = []
        builtins = ['skip', 'break', 'return']
        indent = 0
        block = False
        def lambda2js(expr):
            global block
            if expr.result:
                return '({}) => {}'.format(', '.join([str(x) for x in expr.args]), expr2js(expr.result))
            else:
                block = True
                return '({}) =>'.format(', '.join([str(x) for x in expr.args]))
        def cond2js(cond):
            left = expr2js(cond.left)
            comp = cond.comp
            right = expr2js(cond.right)
            if comp in ['=', 'is']:           comp = '==='
            if comp in ['!=', 'is not']:      comp = '!=='
            if comp in ['>', 'is more than']: comp = '>'
            if comp in ['<', 'is less than']: comp = '<'
            return '{} {} {}'.format(left, comp, right)
        def arr2js(arr):
            return '[' + ', '.join(map(expr2js, arr)) + ']'
        def obj2js(obj):
            js = '{'
            def el2obj(el):
                return expr2js(el[0]) + ': ' + expr2js(el[1])
            js += ', '.join(map(el2obj, obj))
            js += '}'
            return js
        def expr2js(expr, parened=False):
            string = '({})' if parened else '{}'
            global scope
            if type(expr)==Name: return expr.name
            if type(expr)==str: return "'"+expr+"'"
            if type(expr)==int: return str(expr)
            if type(expr)==Regex: return str(expr)
            if type(expr)==Lambda: return string.format(lambda2js(expr))
            if type(expr)==FuncCall: return string.format(funccall2js(expr))
            if type(expr)==Cond: return string.format(cond2js(expr))
            if type(expr)==Array: return arr2js(expr)
            if type(expr)==Object: return obj2js(expr)
            left = expr.left
            if type(left)==Name and left.name=='name':
                left.name = '_name'
            if type(left)==Name and left.name.split('.')[0] not in [*sum(scope, start=[]), *builtins]:
                scope[-1].append(left.name)
            if expr.op:
                op = expr.op
                if op in ['+', 'plus']:                 op = '+'
                if op in ['-', 'minus']:                op = '-'
                if op in ['*', 'times', 'by']:          op = '*'
                if op in ['/', 'over']:                 op = '/'
                if op in ['%', 'mod', 'modulo']:        op = '%'
                right = expr.right
                if type(right)==Name and right.name=='name':
                    right.name = '_name'
                if type(right)==Name and right.name.split('.')[0] not in [*sum(scope, start=[]), *builtins] and op!='.':
                    scope[-1].append(right.name)
                if op=='.':
                    return string.format('{}.{}'.format(expr2js(left, True), expr2js(right, True)))
                return string.format('{} {} {}'.format(expr2js(left, True), op, expr2js(right, True)))
            return string.format(str(left))
        def vardef2js(vardef):
            global scope
            name = vardef.set
            if type(name)==Name and name.name=='name':
                name.name = '_name'
            if type(name)==Name and name.name.split('.')[0] not in [*sum(scope, start=[]), *builtins]:
                scope[-1].append(vardef.set.name)
            if type(vardef.to)==FromLoop:
                return fromloop2js(vardef.to, vardef.set)
            if type(vardef.to)!=Lambda:
                return '{} = {};'.format(name, expr2js(vardef.to))
            else:
                if vardef.to.result:
                    return '{} = {};'.format(name, expr2js(vardef.to))
                else:
                    return '{} = {}'.format(name, expr2js(vardef.to))
        def fromloop2js(loop, variable):
            global block
            block = True
            if variable=='name':
                variable = '_name'
            return 'for ({0} = {1}; {0}++ < {2};)'.format(variable, loop.from_, loop.to_)
        def funccall2js(call):
            name = expr2js(call.name)
            if name=='print' and 'print' not in scope[-1]:
                name = 'console.log'
            if name=='printerror' and 'printerror' not in scope[-1]:
                name = 'console.error'
            if name=='#get':
                name = 'document.querySelector'
            if name=='#id':
                name = 'document.getElementById'
            if name=='name':
                name = '_name'
            if name=='skip':
                return 'continue;'
            if name=='break':
                return 'break;'
            if name=='return':
                return 'return {}'.format(', '.join([expr2js(x) for x in call.args]))
            return '{}({})'.format(name, ', '.join([expr2js(x) for x in call.args]))
        def ifstat2js(stat):
            global block
            block = True
            term = expr2js(stat.term)
            return 'if ({})'.format(term)
        out = ''
        scope.append([])
        for stmt in module.body:
            while stmt.indent<indent:
                indent -= 1
                if len(scope[-1])>0:
                    out += '    '*stmt.indent+'var '+', '.join(scope[-1])+';\n'
                scope = scope[:-1]
                out += '    '*stmt.indent+'}\n'
            while stmt.indent>indent:
                out += ' {\n'
                scope.append([])
                indent += 1
            out += '    '*stmt.indent
            if type(stmt.expr)==VarDef:
                out += vardef2js(stmt.expr)
            if type(stmt.expr)==ElseStat:
                out = out[:-1] + ' else'
                block = True
            if type(stmt.expr)==IfStat:
                out += ifstat2js(stmt.expr)
            if type(stmt.expr)==Name:
                out += funccall2js(FuncCall(stmt.expr, []))
            if type(stmt.expr)==FuncCall:
                out += funccall2js(stmt.expr) + ';'
            if block:
                block = False
            else:
                out += '\n'
        while 0<indent:
            indent -= 1
            if len(scope[-1])>0:
                out += '    '*stmt.indent+'var '+', '.join(scope[-1])+';\n'
            scope = scope[:-1]
            out += '}'
        if len(scope[0])>0:
            defs = 'var '+', '.join(scope[0])+';'
            return defs+'\n'+out
        else:
            return out
    global parse
    parse = reparse(ast)
    print(javascript(parse))
    return str(ast)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='in_file', type=str,
                        help='The input nicescript file')
    parser.add_argument('-o', type=str, default='a.out',
                        help='The output file.')
    args = parser.parse_args()
    with open(args.o, 'w') as fout:
        with open(args.input, 'r') as fin:
            fout.write(perform_actions(fin.read()))
            fin.close()
        fout.close()
