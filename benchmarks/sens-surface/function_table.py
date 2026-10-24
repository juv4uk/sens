#!/usr/bin/env python3
"""#1413: таблиця функцій мови -> TSV для fn_table_bench.

Читає lib/generated/function-table.lisp (ft/2) і пише для кожного рядка:
SENS-код, англійське написання (колонка en, інакше sym, інакше "()").
"""
import re
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
src = (repo / "lib" / "generated" / "function-table.lisp").read_text(encoding="utf-8")


def field(line, key):
    m = re.search(r"\(" + key + r' ("[^"]*"|\(\)|[^()\s]+)\)', line)
    return m.group(1) if m else "()"


out = []
for line in src.splitlines():
    m = re.match(r'\s*\("([01]{8})" ', line)
    if not m:
        continue
    code = m.group(1)
    en = field(line, "en")
    sym = field(line, "sym").strip('"')
    uk = field(line, "ук")
    english = en if en != "()" else (sym if sym not in ("()", "") else "()")
    out.append((code, english, uk))

if not out:
    print("FN_TABLE_EMPTY reason=legacy_eight_bit_rows_absent "
          "source=lib/generated/function-table.lisp actual_rows=0 "
          "expected=canonical_domain_registry_D1_D10", file=sys.stderr)
    sys.exit(1)

target = sys.argv[1] if len(sys.argv) > 1 else "-"
text = "".join(f"{c}\t{e}\t{u}\n" for c, e, u in out)
if target == "-":
    sys.stdout.write(text)
else:
    Path(target).write_text(text, encoding="utf-8")
print(f"рядків: {len(out)}; з англійським написанням: "
      f"{sum(1 for _, e, _ in out if e != '()')}", file=sys.stderr)
