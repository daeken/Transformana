import Transformana

@Transformana.Macro
def testMacro(ast):
	print 'Old AST:', ast
	stmtlist = ast[7][1]
	stmtlist += stmtlist
	return ast

@testMacro
def foo():
	print 'foo'

foo()
print 'New AST:', foo.ast
