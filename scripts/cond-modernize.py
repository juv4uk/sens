"""Історичний сканер тричастинних COND-клауз (лише інвентаризація).

УВАГА: legacy regex-сканер не доводить AST-контекст, D1 PredicateBit,
поточну D3:110 голову, квотування чи полярність NO. Попередній автоматичний
rewrite однаково видаляв expected (1) та (0), підмінюючи NO на YES і
переписуючи .lisp на місці. Це заборонено Contract 11.8 / #5029 / #3170.

--scan зберігається як приблизна карта, а будь-який виклик із файлом
завжди завершується BLOCK (код 4) без запису байтів. Для AST-класифікації
використовуйте #3170 / PR #3182; канонічний .sens admission іде через
scripts/migrate.py тільки після окремих оракулів і CI.
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
    yes = sum(1 for _, _, expected in hits if expected == "(1)")
    no = sum(1 for _, _, expected in hits if expected == "(0)")
    print(f"ІНВЕНТАР (не повний AST-аудит): YES={yes}; NO={no}")
    print("BLOCK: автоматичну заміну вимкнено; немає доказу exact D1/D3 і збереження NO-полярності.")
    print("Джерело не змінено. Далі: #3170 / PR #3182, оракул, scripts/migrate.py.")
    sys.exit(4)

if __name__ == "__main__":
    main()
