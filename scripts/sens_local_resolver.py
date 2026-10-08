#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sens_local_resolver.py — з'єднувальний шар: human spelling -> Local(depth,index).

Проблема (#3135 / #3910 / #4461): джерело .lisp зберігає ІМЕНА (source-shaped), а
машина виконує ЛОКАЛЬНІ як `Local{depth,index}` (crates/sens/src/syntax.rs:103,
environment.rs:306). Мігратор вимагає точних D1-D9 слів і падає на іменах, бо
резолюції `spelling -> Local` для джерела ще немає.

Цей інструмент її робить — і робить ЇЇ ДЕТЕРМІНОВАНО (de Bruijn), НЕ вигадуючи
координат:
  * depth = на скільки lambda-кадрів угору від місця вжитку живе зв'язування;
  * index = позиція параметра в кадрі (0-based).

Кожне НЕрозв'язане ім'я (не параметр у жодному enclosing lambda) є або глобальним
визначенням, або доменним резидентом — воно НЕ локальне, і його долю вирішує
власник (не цей інструмент). Fail-closed: інструмент лише РЕПОРТУЄ такі імена.

Конверт: TAG_LOCAL + varint(depth) + varint(index)  (syntax.rs:250 / 592).
"""
import sys, re, json

TAG_LOCAL = 0x0C  # тег конверта; узгоджується з syntax.rs (TAG_LOCAL)

# --- s-expression reader (source-shaped .lisp) -------------------------------
TOKEN = re.compile(r'\(|\)|;[^\n]*|[^\s()]+')

def read_forms(text):
    toks = [t for t in TOKEN.findall(text) if not t.startswith(';')]
    pos = 0
    def rd():
        nonlocal pos
        t = toks[pos]; pos += 1
        if t == '(':
            items = []
            while toks[pos] != ')':
                items.append(rd())
            pos += 1
            return items
        return t
    forms = []
    while pos < len(toks):
        forms.append(rd())
    return forms

def put_varint(n, out):
    while True:
        b = n & 0x7F; n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n: break

# --- de Bruijn resolution ----------------------------------------------------
def is_exact_word(tok):
    return bool(re.fullmatch(r'[01]{1,9}', tok))

def resolve(form, scope, out, unresolved):
    """scope: list of frames, each a list of param names; index 0 = innermost."""
    if isinstance(form, str):
        if is_exact_word(form):
            out.append(form)              # уже точне D1-D9 слово
            return
        # знайти в найближчому кадрі -> найменший depth
        for depth, frame in enumerate(scope):
            if form in frame:
                index = frame.index(form)
                out.append(('LOCAL', depth, index))
                return
        unresolved.append(form)           # глобал/резидент -> рішення власника
        out.append(('SYMBOL', form))
        return
    # список
    if not form:
        out.append([]); return
    head = form[0]
    # (LAMBDA (params...) body...)
    if isinstance(head, str) and head in ('0010', '00001000', 'lambda', 'LAMBDA') \
       and len(form) >= 3 and isinstance(form[1], list):
        params = form[1]
        inner = []
        newscope = [params] + scope
        for b in form[2:]:
            resolve(b, newscope, inner, unresolved)
        out.append(('LAMBDA', params, inner))
        return
    node = []
    for x in form:
        resolve(x, scope, node, unresolved)
    out.append(node)

def main():
    path = sys.argv[1]
    text = open(path, encoding='utf-8').read()
    forms = read_forms(text)
    out, unresolved = [], []
    for f in forms:
        resolve(f, [], out, unresolved)
    # стислий звіт
    def summarize(node, lvl=0):
        lines = []
        if isinstance(node, tuple):
            if node[0] == 'LOCAL':
                lines.append('  ' * lvl + f"Local(depth={node[1]}, index={node[2]})")
            elif node[0] == 'SYMBOL':
                lines.append('  ' * lvl + f"SYMBOL {node[1]}   <-- не локальне")
            elif node[0] == 'LAMBDA':
                lines.append('  ' * lvl + f"LAMBDA params={node[1]}")
                for b in node[2]:
                    lines += summarize(b, lvl + 1)
            return lines
        if isinstance(node, list):
            lines.append('  ' * lvl + '(')
            for x in node:
                lines += summarize(x, lvl + 1)
            return lines
        lines.append('  ' * lvl + str(node))
        return lines
    print(f"== {path} ==")
    for o in out:
        for l in summarize(o):
            print(l)
    print(f"\nне локальні (глобали/резиденти, рішення власника): {sorted(set(unresolved))}")

if __name__ == '__main__':
    main()
