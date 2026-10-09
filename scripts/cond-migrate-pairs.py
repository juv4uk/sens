import sys, pathlib
COND={"00000111","cond","COND","110"}
def tok(s):
    out=[]; i=0; n=len(s)
    while i<n:
        c=s[i]
        if c==';':
            while i<n and s[i]!='\n': i+=1
        elif c=='"':
            j=i+1
            while j<n and s[j]!='"':
                if s[j]=='\\': j+=1
                j+=1
            out.append(('STR',i,j+1)); i=j+1
        elif c in '()': out.append((c,i,i+1)); i+=1
        elif c.isspace(): i+=1
        else:
            j=i
            while j<n and not s[j].isspace() and s[j] not in '();': j+=1
            out.append((s[i:j],i,j)); i=j
    return out
def parse(ts):
    pos=[0]
    def rd():
        v,st,en=ts[pos[0]]; pos[0]+=1
        if v=='(':
            lst=[]
            while ts[pos[0]][0]!=')': lst.append(rd())
            end=ts[pos[0]][2]; pos[0]+=1
            return {'v':'L','c':lst,'st':st,'en':end}
        return {'v':v,'st':st,'en':en}
    res=[]
    while pos[0]<len(ts): res.append(rd())
    return res
def polof(n):
    if n['v'] in ('1','0'): return 'YES' if n['v']=='1' else 'NO'
    if n['v']=='L':
        a=[x['v'] for x in n['c']]
        if a==[]: return 'NO'
        if a==['1']: return 'YES'
        if a==['0']: return 'NO'
    return 'OTHER'
def isnil(n):
    if n['v']=='L':
        if n['c']==[]: return True
        if len(n['c'])==2 and n['c'][0]['v']=='00000001' and n['c'][1]['v']=='L' and n['c'][1]['c']==[]: return True
    return False
def ren(n):
    if n['v']=='L': return '('+' '.join(ren(c) for c in n['c'])+')'
    return n['v']
def find_clause(node):
    if node['v']!='L': return None
    if node['c'] and node['c'][0]['v'] in COND and len(node['c'])>1:
        cls=node['c'][1:]
        for cl in cls:
            if cl['v']=='L' and len(cl['c'])==3:
                return (cl, cls)
    for c in node['c']:
        r=find_clause(c)
        if r: return r
    return None

src=pathlib.Path(sys.argv[1]).read_text()
steps=0
while True:
    ast=parse(tok(src))
    hit=None
    for t in ast:
        hit=find_clause(t)
        if hit: break
    if not hit: break
    cl, cls = hit
    t,p,b = cl['c']
    P=polof(p)
    sibY=any(polof(o['c'][1])=='YES' and o['c'][0]['v']==t['v'] and ren(o['c'][2])==ren(b) for o in cls if o['v']=='L' and len(o['c'])==3)
    sibN=any(polof(o['c'][1])=='NO' and o['c'][0]['v']==t['v'] and ren(o['c'][2])==ren(b) for o in cls if o['v']=='L' and len(o['c'])==3)
    if P=='NO' and isnil(b):
        # завершальна NO->nil клауза = else; конвенція файлу: (t (00000001 ()))
        if cl is cls[-1]:
            src=src[:cl['st']]+'(t (00000001 ()))'+src[cl['en']:]
        else:
            src=src[:cl['st']]+src[cl['en']:]  # CANDIDATE: drop early-nil (COND defaults to nil)
    elif P=='NO' and sibY:
        src=src[:cl['st']]+src[cl['en']:]
    elif P=='YES' and sibN:
        src=src[:t['st']]+'t'+src[p['en']:]
    elif P=='YES':
        src=src[:p['st']]+src[p['en']:]
    else:
        print("HOLD:", str(cl)[:80]); break
    steps+=1
pathlib.Path(sys.argv[2]).write_text(src)
print(f"steps={steps}  written {sys.argv[2]}")
