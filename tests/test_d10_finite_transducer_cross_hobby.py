# D10 finite-state transducer research oracle
from itertools import product

def run(arcs,state,word):
    out=[]
    for i,sym in enumerate(word):
        key=(state,sym)
        if key not in arcs:
            raise ValueError(f'undefined step {i}')
        state,chunk=arcs[key]
        out.extend(chunk)
    return state,tuple(out)

A={('a',0):('a',()),('a',1):('b',('x','y')),('b',0):('a',('x',)),('b',1):('b',('y',))}
B={(0,'x'):(1,('X',)),(0,'y'):(0,('Y','Z')),(1,'x'):(1,()),(1,'y'):(0,('W',))}

def check():
    assert run(A,'a',())==('a',())
    count=0
    for n in range(6):
        for word in product((0,1),repeat=n):
            for s in ('a','b'):
                whole=run(A,s,word)
                for k in range(len(word)+1):
                    middle,x=run(A,s,word[:k]); end,y=run(A,middle,word[k:]); assert (end,x+y)==whole
                t1,mid=whole; t2,output=run(B,0,mid)
                assert t2 in (0,1)
                count+=1
    try: run({('a',0):('a',())},'a',(0,1))
    except ValueError as e: assert 'step 1' in str(e)
    else: raise AssertionError('missing edges must fail')
    assert count==126
    print('FINITE-TRANSDUCER: 126 inputs; every chunk boundary preserves state/output; undefined edge rejects')

if __name__=='__main__': check()
