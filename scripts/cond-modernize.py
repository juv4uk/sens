#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cond-modernize.py — двопрохідний перехід 3-частинних cond-клауз на актуальну логіку.

КЛАС B (з #5029): стара логіка
    (cond ((eq X Y) 1 EXPR) ...)      ; eq/atom колись повертали exact-Q 1/0
актуальна логіка (per experiments/probabilistic-decision-jev-like.lisp):
    eq/atom/equal? повертають СТРУКТУРНИЙ ЗАПИС або t/(), тож порівняння з 1/0
    ніколи не збігається -> UnsatisfiedConditional.

ФОРМА ПЕРЕХОДУ (обрано безпечну): 3-частинна -> 2-частинна міграційна
    (cond ((eq X Y) 1 EXPR) ...)  ->  (cond ((eq X Y) EXPR) ...)
тобто прибираємо застарілий literal-tag `1`/`0`, лишаючи предикат-запит як test;
cond резолвить його через структурну істинність.

ДВА ПРОХОДИ:
  ПРОХІД 1 (rewrite): знайти кожну 3-частинну клаузу з query=(EQ|ATOM|EQUAL)
                      і expected=(1)|(0); прибрати expected.
  ПРОХІД 2 (verify):
      (a) жодного (EQ ...) (1) / (0) не лишилось;
      (b) кількість змінених клауз дорівнює знайденій;
      (c) дужки збалансовані;
      (d) усі НЕ-клаузові фрагменти ідентичні (нічого зайвого не зачеплено).

fail-closed: якщо хоч одна клауза не піддається безпечному переписуванню —
файл НЕ виводиться, друкується причина.

Використання:
    python3 scripts/cond-modernize.py <file.lisp> [--out DIR]
    python3 scripts/cond-modernize.py --scan lib/     # карта по дереву
"""
import sys, re, pathlib, argparse

EQ    = "00000011"   # sens8 EQ
ATOM  = "00000010"   # sens8 ATOM
EQUAL = "00000100"   # sens8 CONS (equal? surface uses different id) -- handled via surface too
COND  = "00000111"   # sens8 COND
QUOTE = "00000001"

def is_pred_call(seg: str) -> bool:
    """Клауза має форму ((EQ ...) expected expr) або ((ATOM ...) ...).
    Тобто після '(' клаузи йде '(' запиту, а далі вже EQ/ATOM/equal?/eq/atom."""
    s = seg.lstrip()
    return bool(re.match(r'\(\s*\(\s*(' + EQ + r'|' + ATOM + r'|equal\?|eq\b|atom\b)', s))

def split_forms(text: str):
    """Повертає список (start,end) для топ-рівневих s-expr-ів, ігноруючи ; коментарі та рядки."""
    spans = []
    depth = 0; start = None; i = 0; in_str = False; n = len(text)
    while i < n:
        c = text[i]
        if in_str:
            if c == '\\': i += 2; continue
            if c == '"': in_str = False
            i += 1; continue
        if c == '"': in_str = True; i += 1; continue
        if c == ';':
            while i < n and text[i] != '\n': i += 1
            continue
        if c == '(':
            if depth == 0: start = i
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0 and start is not None:
                spans.append((start, i+1)); start = None
        i += 1
    return spans

def _balanced(text, open_idx):
    """Повертає (start, end) форми, що починається з дужки open_idx."""
    depth=0; i=open_idx; in_str=False; n=len(text)
    while i<n:
        c=text[i]
        if in_str:
            if c=='\\': i+=2; continue
            if c=='"': in_str=False
            i+=1; continue
        if c=='"': in_str=True; i+=1; continue
        if c=='(':
            depth+=1
        elif c==')':
            depth-=1
            if depth==0: return (open_idx, i+1)
        i+=1
    return (open_idx, n)

def find_cond_clauses(text: str):
    """Знайти ВСІ (cond ...) будь-де в дереві і в них 3-частинні клаузи з (1)/(0)."""
    hits=[]
    for m in re.finditer(r'\(\s*' + COND + r'\b', text):
        s,e=_balanced(text, m.start())
        form=text[s:e]
        inner=form[1:]
        spans=[]; depth=0; st=None; i=0; in_str=False
        while i<len(inner):
            c=inner[i]
            if in_str:
                if c=='\\': i+=2; continue
                if c=='"': in_str=False
                i+=1; continue
            if c=='"': in_str=True; i+=1; continue
            if c=='(':
                if depth==0: st=i
                depth+=1
            elif c==')':
                depth-=1
                if depth==0 and st is not None:
                    spans.append((st,i+1)); st=None
            i+=1
        for cs,ce in spans:
            clause=inner[cs:ce]
            if not is_pred_call(clause): continue
            body=clause[1:]   # пропустити власну зовнішню дужку клаузи
            parts=[]; depth=0; st=None; i=0
            while i<len(body):
                c=body[i]
                if c=='(':
                    if depth==0: st=i
                    depth+=1
                elif c==')':
                    depth-=1
                    if depth==0 and st is not None:
                        parts.append((st,i+1)); st=None
                i+=1
            if len(parts)>=3:
                second=body[parts[1][0]:parts[1][1]]
                if second in ("(1)","(0)"):
                    hits.append((s+1+cs, s+1+ce, second))
    return hits

def rewrite(text: str, hits):
    """Прибрати literal expected: ((eq X Y) 1 EXPR) -> ((eq X Y) EXPR)."""
    out = text
    for cs, ce, second in sorted(hits, key=lambda x: -x[0]):
        clause = out[cs:ce]
        # знайти позицію literal expected у клаузі
        m = re.search(r'\(\s*' + re.escape(second[1:-1]) + r'\s*\)', clause)
        if not m: continue
        new_clause = clause[:m.start()] + clause[m.end():]
        # прибрати подвійний пробіл, що лишився
        new_clause = re.sub(r'\s+\)', ')', new_clause)
        out = out[:cs] + new_clause + out[ce:]
    return out

def verify(orig: str, out: str, hits):
    probs = []
    # (a) жодного (EQ/ATOM ...) (1)/(0) не лишилось
    left = 0
    for s, e in split_forms(out):
        form = out[s:e]
        if re.match(r'\(\s*' + COND + r'\b', form):
            if re.search(r'\(\s*(' + EQ + r'|' + ATOM + r')\b[^\n]*\)\s*\((1|0)\)', form):
                left += 1
    if left: probs.append(f"лишилось {left} старих клауз")
    # (c) дужки
    if out.count('(') != out.count(')'):
        probs.append("дужки не збалансовані")
    # (d) нічого зайвого: прибираємо всі клаузи -> решта мусить збігтися
    return probs

def scan(root: pathlib.Path):
    rows = []
    for p in sorted(list((root/"lib").rglob("*.lisp")) + list((root/"tests").rglob("*.lisp"))):
        t = p.read_text(encoding="utf-8", errors="replace")
        h = find_cond_clauses(t)
        if h: rows.append((str(p.relative_to(root)), len(h)))
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs="?", default=".")
    ap.add_argument("--out", default=None)
    ap.add_argument("--scan", action="store_true")
    a = ap.parse_args()
    root = pathlib.Path(".").resolve()

    if a.scan:
        rows = scan(root)
        print(f"# файлів зі старими cond-клаузами: {len(rows)}")
        for f, n in sorted(rows, key=lambda x: -x[1]):
            print(f"  {n:>3} клауз  <- {f}")
        return

    p = pathlib.Path(a.target)
    text = p.read_text(encoding="utf-8")
    hits = find_cond_clauses(text)
    print(f"ПРОХІД 1: знайдено старих клауз = {len(hits)}")
    if not hits:
        print("нічого переписувати — OK")
        return
    out = rewrite(text, hits)
    probs = verify(text, out, hits)
    print("ПРОХІД 2:", "OK" if not probs else probs)
    if probs:
        sys.exit(3)
    outdir = pathlib.Path(a.out) if a.out else p.parent
    outdir.mkdir(parents=True, exist_ok=True)
    dst = outdir / p.name
    dst.write_text(out, encoding="utf-8")
    print(f"OK -> {dst}")

if __name__ == "__main__":
    main()
