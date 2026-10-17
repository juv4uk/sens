#!/usr/bin/env python3
"""Звіт: скільки .lisp-коду вже на повній українській проєкції `укр`.

`укр` — повна українська peer surface (docs/superpowers/plans/2026-09-13-full-uk-cyrillic-surface.md).
Доменні таблиці й реєстр несуть пари `(ук …) (укр …)`: коротку й повну форми.
Рядок вважається **переведеним на проєкцію `укр`**, коли обидві форми збігаються
(`ук == укр`), тобто коротка форма вже піднята до повної.

Детермінований, лише читання. Друкує людський рядок і — для видимості в CI —
червону анотацію GitHub (`::error::`). Код виходу 0: це *прогрес*, а не вердикт;
щоб зробити його жорстким, досить перевірити відсоток вище порога.

Використання: python3 scripts/report_ukr_projection_progress.py [--root DIR] [--json OUT]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAIR = re.compile(
    r"\(ук\s+(\(\)|\"(?:\\.|[^\"\\])*\"|[^()\s]+)\)\s+"
    r"\(укр\s+(\(\)|\"(?:\\.|[^\"\\])*\"|[^()\s]+)\)"
)
CYRILLIC = re.compile(r"[а-яїієґА-ЯЇІЄҐ]")
TOKEN = re.compile(r"[^\s()'\"]+")


def strip_comments_and_strings(text: str) -> str:
    """Remove ; comments and "…" strings so only code tokens remain."""
    out, i, n, in_string = [], 0, len(text), False
    while i < n:
        ch = text[i]
        if in_string:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == ";":
            j = text.find("\n", i)
            i = n if j < 0 else j + 1
            continue
        if ch == '"':
            in_string = True
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def latin_identifiers(code: str) -> set[str]:
    """Latin-bearing code tokens, ignoring pure binary/bits words."""
    found = set()
    for m in TOKEN.finditer(code):
        w = m.group(0)
        if re.search(r"[A-Za-z]", w) and not re.fullmatch(r"[#:]?[01]+", w):
            found.add(w)
    return found


def measure(root: Path) -> dict:
    files = sorted(p for p in root.rglob("*.lisp") if ".git" not in p.parts)
    pairs_total = pairs_same = 0
    files_with_pairs = 0
    files_ukrainian = 0
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        matches = list(PAIR.finditer(text))
        if matches:
            files_with_pairs += 1
            pairs_total += len(matches)
            pairs_same += sum(1 for m in matches if m.group(1) == m.group(2))
        code = strip_comments_and_strings(text)
        if CYRILLIC.search(code):
            files_ukrainian += 1
    pct_pairs = (100.0 * pairs_same / pairs_total) if pairs_total else 0.0
    pct_files = (100.0 * files_ukrainian / len(files)) if files else 0.0
    return {
        "lisp_files": len(files),
        "pairs_total": pairs_total,
        "pairs_same": pairs_same,
        "pairs_pct": round(pct_pairs, 1),
        "files_with_pairs": files_with_pairs,
        "files_ukrainian": files_ukrainian,
        "files_pct": round(pct_files, 1),
    }


def render(m: dict) -> str:
    return (
        f"УКР-ПРОЄКЦІЯ .lisp: поверхневі пари ук==укр "
        f"{m['pairs_same']}/{m['pairs_total']} ({m['pairs_pct']}%) "
        f"у {m['files_with_pairs']} файлах; "
        f".lisp-файлів з укр-поверхнею {m['files_ukrainian']}/{m['lisp_files']} "
        f"({m['files_pct']}%)"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--json", default=None, help="додатково записати JSON-звіт")
    ap.add_argument("--min-pairs-pct", type=float, default=None,
                    help="якщо задано, код виходу 1 при меншому відсотку (жорсткий режим)")
    args = ap.parse_args()

    m = measure(Path(args.root))
    line = render(m)
    print(line)
    # Червоне для видимості в CI (анотація, не вердикт).
    print(f"::error::{line}")
    if args.json:
        Path(args.json).write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
    if args.min_pairs_pct is not None and m["pairs_pct"] < args.min_pairs_pct:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
