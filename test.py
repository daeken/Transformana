from __future__ import with_statement
from Transformana import TransformNodes, Compare

def rewriteCondition(matching, cond):
	return Compare(matching, [('==', cond)])

@TransformNodes('with')
def switchMacro(ast):
	withTarget = ast[1]
	assert withTarget[0] == 'callfunc' and withTarget[1] == ['name', 'switch']
	
	matching = withTarget[2][0]
	body = ast[3][1][0]
	assert body[0] == 'if'
	
	body[1] = map(list, body[1]) # Turn case tuples into lists
	for conds in body[1]:
		conds[0] = rewriteCondition(matching, conds[0])
	
	return body

@switchMacro
def test(foo):
	with switch(foo):
		if 0:
			return 'Hello world!'
		elif 1:
			return 'Yep, working.'
		else:
			return 'Don\'t know.'

print test(0)
print test(1)
print test(2)
