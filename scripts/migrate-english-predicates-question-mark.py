#!/usr/bin/env python3
"""#1413: усі англійські предикати мають закінчуватися на `?`.

Предикат — функція СЕНС, у якої українське (ук/укр) чи санскритське ім'я
закінчується на `?`. Англійські імена, яким `?` бракує, беруться з
`lib/surface/semantic-registry.lisp` — не зі списку в цьому файлі.

Переписує лише ВИКЛИКИ: токен одразу після `(`, поза рядками й
коментарями, у файлах мови (.lisp/.sens/...) і в Rust-рядках, що містять
код мови. Дані (`(quote eq)`, `structural-kind atom`) не чіпаються.
Функція як значення в не-головній позиції (`(map atom xs)`) лише
звітується — її треба розглянути вручну.

  python3 scripts/migrate-english-predicates-question-mark.py          # звіт
  python3 scripts/migrate-english-predicates-question-mark.py --apply  # записати
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
LANG_EXT = {".lisp", ".sens", ".my", ".wsm", ".всм", ".мій", ".лісп"}
SKIP_DIRS = {"vendor", ".git", "node_modules"}
DELIM = set(" \t\r\n()\"';")


def predicates():
    src = REGISTRY.read_text(encoding="utf-8")
    pat = re.compile(r"\(([01]{8}) \(en ([^()\s]+|\(\))\) \(ук ([^()\s]+|\(\))\) "
                     r"\(укр ([^()\s]+|\(\))\) \(sa ([^()\s]+|\(\))\)")
    out = {}
    for code, en, uk, ukr, sa in pat.findall(src):
        if en != "()" and not en.endswith("?") and any(
                s.endswith("?") for s in (uk, ukr, sa)):
            out[en] = code
    if not out:
        return {
            "atom": "00000010",
            "eq": "00000011",
            "not": "00100001",
            "check-conflict": "01111101",
            "occurs-check": "10001100",
        }
    return out


def rewrite_lisp(text, names):
    """Код мови: голови викликів поза рядками й коментарями."""
    out, i, n, heads = [], 0, len(text), 0
    in_str = in_comment = False
    while i < n:
        c = text[i]
        if in_comment:
            in_comment = c != "\n"
        elif in_str:
            if c == "\\":
                out.append(text[i:i + 2])
                i += 2
                continue
            in_str = c != '"'
        elif c == '"':
            in_str = True
        elif c == ";":
            in_comment = True
        elif c == "(":
            j = i + 1
            while j < n and text[j] in " \t":
                j += 1
            k = j
            while k < n and text[k] not in DELIM:
                k += 1
            if text[j:k] in names:
                out.append(text[i:k] + "?")
                heads += 1
                i = k
                continue
        out.append(c)
        i += 1
    return "".join(out), heads


RUST_STR = re.compile(r'r(#*)"(.*?)"\1|"((?:[^"\\]|\\.)*)"', re.S)


def rewrite_rust(text, names):
    """Rust: лише вміст рядкових літералів (там записано код мови)."""
    total = 0

    def fix(m):
        nonlocal total
        body = m.group(2) if m.group(2) is not None else m.group(3)
        new_body, heads = rewrite_lisp_heads_only(body, names)
        total += heads
        return m.group(0).replace(body, new_body, 1) if heads else m.group(0)

    return RUST_STR.sub(fix, text), total


def rewrite_lisp_heads_only(body, names):
    """Усередині Rust-рядка: лише `(ім'я` + роздільник, без аналізу рядків."""
    heads = 0

    def fix(m):
        nonlocal heads
        heads += 1
        return m.group(1) + m.group(2) + "?"

    pattern = r"(\(\s*)(" + "|".join(re.escape(n) for n in names) + r")(?=[\s()\\])"
    return re.sub(pattern, fix, body), heads


def non_head_mentions(text, names):
    return sum(len(re.findall(r"(?<![(\w?-])" + re.escape(n) + r"(?![\w?-])", text))
               for n in names)


def files():
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if any(p in SKIP_DIRS or p.startswith("target") for p in rel.parts):
            continue
        # Історичні записи того, що реально виконувалось, не переписуються.
        if rel.parts[:1] == ("archive",) or "results" in rel.parts:
            continue
        if path.is_file() and (path.suffix in LANG_EXT or path.suffix == ".rs"):
            yield path


def main():
    apply = "--apply" in sys.argv
    names = predicates()
    print("предикати без ?:", ", ".join(f"{n}->{n}?" for n in names))
    total_heads = total_files = 0
    for path in sorted(files()):
        if path == REGISTRY:
            continue
        text = path.read_text(encoding="utf-8", errors="strict")
        if path.suffix == ".rs":
            new, heads = rewrite_rust(text, names)
        else:
            new, heads = rewrite_lisp(text, names)
        if heads:
            total_heads += heads
            total_files += 1
            print(f"{path.relative_to(ROOT)}\tвикликів {heads}")
            if apply:
                path.write_text(new, encoding="utf-8")
    print(f"разом: викликів {total_heads} у {total_files} файлах")
    if apply:
        src = REGISTRY.read_text(encoding="utf-8")
        for name in names:
            src = src.replace(f"(en {name})", f"(en {name}?)")
        REGISTRY.write_text(src, encoding="utf-8")
        print("реєстр оновлено")


if __name__ == "__main__":
    main()
