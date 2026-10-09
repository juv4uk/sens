"""Independent finite-state composition witness (not SENS interpreter parity)."""
from itertools import product
from test_d10_finite_transducer_cross_hobby import run, A, B

def compose(a,b):
    aa=set(x for x,_ in a)
    bb=set(x for x,_ in b)
    result={}
    for s in aa:
        for t in bb:
            for (current,symbol),(nxt,mid) in a.items():
                if current!=s: continue
                try: end, out = run(b,t,mid)
                except ValueError: continue
                result[((s,t),symbol)]=((nxt,end),out)
    return result

def check():
    combined=compose(A,B)
    count=0
    for size in range(6):
        for inputs in product((0,1), repeat=size):
            for s in ('a','b'):
                for t in (0,1):
                    next1, mid=run(A,s,inputs)
                    next2, output=run(B,t,mid)
                    assert run(combined,(s,t),inputs)==((next1,next2),output)
                    count+=1
    assert count==252
    bad=compose(A,{(0,'x'):(0,('ok',))})
    try: run(bad,('a',0),(1,))
    except ValueError: pass
    else: raise AssertionError('incomplete composition accepted')
    print('FINITE COMPOSITION: 252 cascade/product equivalences; missing-edge veto')

if __name__=='__main__': check()
