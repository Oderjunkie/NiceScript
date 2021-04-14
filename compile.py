#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
from iteration_utilities import deepflatten
from parsimonious import Grammar, NodeVisitor
import parsimonious.nodes as pNodes

grammar = Grammar(r"""
module = ( NEWLINE? ((COMMENT / statement) (NEWLINE (COMMENT / statement))* NEWLINE?)? )

statement = INDENT* expr_func

INDENT = ~" {4}"
EQU = "="/"is"
NOTEQU = "!="/"is not"
GT = ">"/"is more than"
GTE = ">="/"is more than or equal to"
LT = "<"/"is less than"
LTE = "<="/"is less than or equal to"
PLUS = "+"/("plus"/"and"/"with")
MINUS = "-"/("minus"/"without")
TIMES = "*"/("times"/"by")
ON = "/"/("on"/"over")
MOD = "%"/("mod"/"modulo")
comparison = LTE / GTE / LT / GT / NOTEQU / EQU
value = NUMBER / STRING / REGEX / function / IDENTIFIER

cond = ( expr WHITESPACE? comparison WHITESPACE? expr )

algebraic_op = PLUS/MINUS/TIMES/ON/MOD

fromloop = ( "from" WHITESPACE expr WHITESPACE "to" WHITESPACE expr )
vardef = ( IDENTIFIER WHITESPACE? EQU WHITESPACE? expr )
functioncall = IDENTIFIER (WHITESPACE expr)+
ifstat = "if" WHITESPACE (cond / expr)
function = IDENTIFIER (WHITESPACE IDENTIFIER)* WHITESPACE? '->' WHITESPACE? expr_func?

expr_func = vardef
          / function
          / fromloop
          / ifstat
          / functioncall
          / ( value WHITESPACE algebraic_op WHITESPACE value )
          / ( value '[' WHITESPACE? value WHITESPACE? ']' )
          / ( value )

expr = vardef
     / function
     / fromloop
     / ifstat
     / ( value WHITESPACE algebraic_op WHITESPACE value )
     / ( value '[' WHITESPACE? value WHITESPACE? ']' )
     / ( value )

STRING = ~"(\".*?\")|('.*?\')|(`.*?`)"s
NUMBER = (~"[0-9]+") / (~"0x([0-9A-F]|[0-9a-f])*")
REGEX = ~"\/([^\/]|\\\/)*?\/"
IDENTIFIER = ~"[a-zA-Z_$#][a-zA-Z0-9_$#\.]*"
NEWLINE = ~"(\r|\n|\r\n)+"
WHITESPACE = ~"[ \t]+"
COMMENT = INDENT* ~"\/\*.*?\*\/"s
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
            return '    '*self.indent+'if {}'.format(str(self.term))
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
            return '{}'.format(self.left.text)
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
                        #print(part)
                        if part.text.strip()=='':
                            continue
                    except Exception as e:
                        print(e, type(part))
                        if part.strip()=='':
                            continue
                    final.append(part)
                return VarDef(Name(final[0].text), final[-1])
            except Exception as e:
                print('VarDef error: {}'.format(e))
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
                assert visited_children[0].expr_name=='IDENTIFIER'
                final = FuncCall(Name(visited_children[0].text), args)                return final
            except Exception as e:
                print('FunctionCall error: {}'.format(e))
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
        def visit_value(self, node, visited_children):
            text = visited_children
            try:
                while type(text)==list:
                    text = text[0]
                if text.expr_name=='IDENTIFIER':
                    return Name(text.text)
                if text.expr_name=='STRING':
                    return text.text[1:-1]
                num = float(text.text)
                if int(num)==num:
                    num = int(num)
                return num
            except Exception as e:
                print('Value error: {}'.format(e))
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
                        return thing[0].text
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
                            return thing[0].text
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
                            #print(part)
                            cleaned.append(part)
                    except Exception:
                        pass
                    if cleaned:
                        try:
                            finals.append(cleaned[0])
                        except Exception:
                            pass
                #print('\n\n\n\n-----------------')
                #for part in finals:
                #    print(part, type(part), end='\n\n')
                #print(finals[0], finals[1].text, finals[2])
                return Expr(finals[0], finals[1].text, finals[2])
                #for part in thing:
                #    print('-------------------')
                #    print(part)
            except Exception as e:
                #print('ExprFunc error: {}'.format(e))
                return finals[0]
        def visit_cond(self, node, visited_children):
            part = visited_children or node
            left = part[0]
            comp = part[2][0][0].text
            right = part[4][0]
            if type(left) in [int, float]:
                left = Expr(left)
            if type(right) in [int, float]:
                right = Expr(right)
            return Cond(left, comp, right)
        def visit_ifstat(self, node, visited_children):
            part = visited_children or node
            #print(repr(part[2][0]))
            return IfStat(part[2][0])
            #pprint()
            #exit()
            #return part
        def generic_visit(self, node, visited_children):
            return visited_children or node
    def reparse(tree):
        newtree = TrickOrTreater().visit(tree)
        return newtree
    def javascript(module):
        global block
        scope = []
        builtins = ['print', 'skip', 'break']
        indent = 0
        block = False
        def lambda2js(expr):
            return '({}) => {}'.format(', '.join([str(x) for x in expr.args]), expr2js(expr.result))
        def cond2js(cond):
            left = expr2js(cond.left)
            comp = cond.comp
            right = expr2js(cond.right)
            if comp in ['=', 'is']: comp = '==='
            if comp in ['!=', 'is not']: comp = '!=='
            if comp in ['>', 'is more than']: comp = '>'
            if comp in ['<', 'is less than']: comp = '<'
            if comp in ['>=', 'is more than or equal to']: comp = '>='
            if comp in ['<=', 'is less than or equal to']: comp = '<='
            return '{} {} {}'.format(left, comp, right)
        def expr2js(expr):
            #print(repr(expr))
            if type(expr)==Name: return str(expr)
            if type(expr)==str: return "'"+expr+"'"
            if type(expr)==Lambda: return lambda2js(expr)
            if type(expr)==FuncCall: return funccall2js(expr)
            if type(expr)==Cond: return cond2js(expr)
            left = expr.left
            if type(left)==Name and left.name not in [*scope, *builtins]:
                scope.append(left.name)
            #print('AAAAAAa')
            if expr.op:
                op = expr.op
                if op in ['+', 'plus', 'and', 'with']:  op = '+'
                if op in ['-', 'minus', 'without']:     op = '-'
                if op in ['*', 'times', 'by']:          op = '*'
                if op in ['/', 'on', 'over']:           op = '/'
                if op in ['%', 'mod', 'modulo']:        op = '%'
                right = expr.right
                if type(right)==Name and right.name not in [*scope, *builtins]:
                    scope.append(right.name)
                #print(left, op, right)
                return '{} {} {}'.format(left, op, right)
            return str(left)
        def vardef2js(vardef):
            if type(vardef.set)==Name and vardef.set.name not in [*scope, *builtins]:
                scope.append(vardef.set.name)
            if type(vardef.to)==FromLoop:
                return fromloop2js(vardef.to, vardef.set)
            return '{} = {};'.format(vardef.set, expr2js(vardef.to))
        def fromloop2js(loop, variable):
            global block
            block = True
            return 'for ({0} = {1}; {0}++ < {2};)'.format(variable, loop.from_, loop.to_)
        def funccall2js(call):
            name = call.name.name
            if name=='print':
                name = 'console.log'
            if name=='$':
                name = 'document.querySelector'
            if name=='skip':
                return 'continue;'
            if name=='break':
                return 'break;'
            return '{}({})'.format(name, ', '.join([expr2js(x) for x in call.args]))
        def ifstat2js(stat):
            global block
            block = True
            term = expr2js(stat.term)
            return 'if ({})'.format(term)
        out = ''
        for stmt in module.body:
            while stmt.indent<indent:
                indent -= 1
                out += '    '*stmt.indent+'}\n'
            while stmt.indent>indent:
                out += ' {\n'
                indent += 1
            out += '    '*stmt.indent
            if type(stmt.expr)==VarDef:
                out += vardef2js(stmt.expr)
            if type(stmt.expr)==IfStat:
                out += ifstat2js(stmt.expr)
            if type(stmt.expr)==Name:
                out += funccall2js(FuncCall(stmt.expr, []))
            if type(stmt.expr)==FuncCall:
                out += funccall2js(stmt.expr) + ';'
            if block:
                block = False
            else:
                #out += ' // ' + str(stmt.expr) + '\n'
                out += '\n'
        while 0<indent:
            indent -= 1
            out += '}'
        if scope:
            defs = 'var '+', '.join(scope)+';'
            return defs+'\n'+out
        else:
            return out
##    def javascript(module):
##        global inline
##        scope = []
##        inline = False
##        builtins = ['print', 'skip', 'break']
##        def expr2js(expr):
##            if type(expr)==list:
##                for part in expr:
##                    while type(part)==list:
##                        part = part[-1]
##                    print(type(part))
##                return exit()
##            if type(expr.left)==Name and expr.left.name not in [*scope, *builtins]:
##                    scope.append(expr.left.name)
##            if expr.op:
##                op = expr.op.text
##                if op in ['+', 'plus', 'and', 'with']:
##                    op = '+'
##                elif op in ['-', 'minus', 'without']:
##                    op = '-'
##                elif op in ['*', 'times', 'by']:
##                    op = '*'
##                elif op in ['/', 'on', 'over']:
##                    op = '/'
##                elif op in ['%', 'mod']:
##                    op = '%'
##                if type(expr.right)==Name and expr.right.name not in [*scope, *builtins]:
##                    scope.append(expr.right.name)
##                left = expr.left
##                right = expr.right
##                if type(left)==Name:
##                    left = left.name
##                else:
##                    try:
##                        if left.expr_name in ['STRING', 'REGEX']:
##                            left = left.text
##                        else:
##                            left = int(left)
##                    except:
##                        left = int(left)
##                if type(right)==Name:
##                    right = right.name
##                else:
##                    try:
##                        if right.expr_name in ['STRING', 'REGEX']:
##                            right = right.text
##                        else:
##                            right = int(right.text)
##                    except:
##                        right = right.text
##                return '{} {} {}'.format(left, op, right)
##            else:
##                if type(expr.left)==Name:
##                    return expr.left.name
##                else:
##                    try:
##                        if expr.left.expr_name in ['STRING', 'REGEX']:
##                            return expr.left.text
##                        else:
##                            return int(expr.left.text)
##                    except:
##                        return int(expr.left.text)
##        def vardef2js(vardef):
##            global inline
##            if vardef.set not in [*scope, *builtins]:
##                    scope.append(vardef.set)
##            if type(vardef.to)==FromLoop:
##                inline = True
##                return 'for ({0} = {1}; {0}++ < {2};) '.format(vardef.set, vardef.to._from, vardef.to._to)
##            else:
##                return '{} = {};\n'.format(vardef.set, expr2js(vardef.to))
##        def if2js(ifstat):
##            global inline
##            inline = True
##            if ifstat.op:
##                op = ifstat.op.text
##                if op in ['is', '=']: op = '=='
##                if op in ['is not', '!=']: op = '!='
##                if op in ['is less than', '<']: op = '<'
##                if op in ['is more than', '>']: op = '>'
##                if op in ['is less than or equal to', '<=']: op = '<='
##                if op in ['is more than or equal to', '>=']: op = '>='
##                return 'if ({} {} {}) '.format(expr2js(ifstat.left), op, expr2js(ifstat.right))
##            else:
##                return 'if ({}) '.format(expr2js(ifstat.left))
##        def func2js(funccall):
##            name = funccall.name
##            if name=='skip':
##                return 'continue;\n'
##            if name=='break':
##                return 'break;\n'
##            if funccall.name not in [*scope, *builtins]:
##                scope.append(funccall.name)
##            if name=='print':
##                name = 'console.log'
##            if name=='$':
##                name = 'document.querySelector'
##            return '{}({});\n'.format(name, ', '.join([expr2js(x) for x in funccall.args]))
##        lastindent = 0
##        code = ''
##        for stmt in module.body:
##            if stmt.indent!=lastindent:
##                if abs(stmt.indent-lastindent)>1:
##                    raise IndentationError()
##                if stmt.indent>lastindent:
##                    if inline:
##                        inline = False
##                        code += '{\n'
##                    else:
##                        code += '    '*stmt.indent+'{\n'
##                else:
##                    if inline:
##                        inline = False
##                        code += '}\n'
##                    else:
##                        code += '    '*stmt.indent+'}\n'
##                lastindent = stmt.indent
##            if type(stmt)==VarDef:
##                code += '    '*stmt.indent+vardef2js(stmt)
##            elif type(stmt)==IfStat:
##                code += '    '*stmt.indent+if2js(stmt)
##            elif type(stmt)==FuncCall:
##                code += '    '*stmt.indent+func2js(stmt)
##        if lastindent!=0:
##                if lastindent>1:
##                    raise SyntaxError('uhhhh')
##                code += '}\n'
##        scope = [x for x in scope if '.' not in x and '#' not in x]
##        if len(scope)>0:
##            code = 'var '+', '.join(scope)+';\n'+code
##        return code
    #print(repr(reparse(ast)))
    global parse
    parse = reparse(ast)
    print(javascript(parse))
    return str(ast)

if __name__ == '__main__':
    with open('a.out', 'w') as fout:
        with open('codetest.txt', 'r') as fin:
            fout.write(perform_actions(fin.read()))
            fin.close()
        fout.close()
    #parser = argparse.ArgumentParser()
    #parser.add_argument('input', metavar='in_file', type=str,
    #                    help='The input nicescript file')
    #parser.add_argument('-o', type=str, default='a.out',
    #                    help='The output file.')
    #args = parser.parse_args()
    #with open(args.o, 'w') as fout:
    #    with open(args.input, 'r') as fin:
    #        fout.write(perform_actions(fin.read()))
    #        fin.close()
    #    fout.close()
