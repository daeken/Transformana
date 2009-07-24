import sys, compiler, copy, inspect, os
import compiler.ast as pyast

class Exp(list):
	def __init__(self, *x):
		list.__init__(self, [self.__class__.__name__] + list(x))

astNodes = dict()
for name in dir(pyast):
	obj = getattr(pyast, name)
	if inspect.isclass(obj) and issubclass(obj, pyast.Node):
		astNodes[name.lower()] = obj
		globals()[name] = type(name.lower(), (Exp, ), {})

def astToExp(ast):
	if isinstance(ast, pyast.Node):
		return eval(`ast`)
	else:
		return ast

def expToAst(exp):
	if isinstance(exp, Exp):
		nodeCls = astNodes[exp[0]]
		args = map(expToAst, exp[1:])
		return nodeCls(*args)
	elif isinstance(exp, list) or isinstance(exp, tuple):
		return map(expToAst, exp)
	else:
		return exp

def search(ast, type):
	if not isinstance(ast, list) and not isinstance(ast, tuple):
		return
	
	if isinstance(ast, Exp) and ast[0] == type:
		yield ast
	
	for node in ast:
		for found in search(node, type):
			yield found

def transform(ast, type, func):
	if not isinstance(ast, list):
		return ast
	
	if isinstance(ast, Exp) and ast[0] == type:
		new = func(ast)
		if new != None:
			ast = new
	
	for i, node in enumerate(ast):
		ast[i] = transform(node, type, func)
	
	return ast

def findFunction(ast, func):
	code = func.func_code
	name = code.co_name
	
	for func in search(ast, 'function'):
		if func[2] == name:
			return func

class Macro(object):
	def __init__(self, func):
		self.func = func
	
	def __call__(self, subfunc):
		if hasattr(subfunc, 'ast'):
			funcAst = subfunc.ast
		else:
			code = subfunc.func_code
			fn = os.path.abspath(code.co_filename)
			if fn.endswith('.pyc'):
				fn = fn[:-1]
			try:
				ast = compiler.parse(file(fn, 'r').read())
			except IOError:
				return
			
			ast = astToExp(ast)
			funcAst = findFunction(ast, subfunc)
			
			funcAst[1] = None # Kill the function's decorators
		
		new = self.func(copy.deepcopy(funcAst))
		if new == None or funcAst == new:
			subfunc.ast = funcAst
			return subfunc
		
		if not isinstance(new, Exp) and not isinstance(new, list):
			return new
		
		name = subfunc.func_code.co_name
		ast = expToAst(new)
		stmts = [
				ast, 
				pyast.Discard(pyast.CallFunc(pyast.Name('__func__'), [pyast.Name(name)], None, None))
			]
		ast = pyast.Module(None, pyast.Stmt(stmts))
		compiler.misc.set_filename(subfunc.func_code.co_filename, ast)
		module = compiler.pycodegen.ModuleCodeGenerator(ast).getCode()
		eval(module, dict(__func__=self.__funcReturn__))
		subfunc.func_code = self.newfunc.func_code
		
		subfunc.ast = new
		return subfunc
	
	def __funcReturn__(self, newfunc):
		self.newfunc = newfunc

def TransformNodes(type):
	def subtrans(func):
		def transformBody(ast):
			return transform(ast, type, func)
		return Macro(transformBody)
	
	return subtrans
