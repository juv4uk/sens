#!/usr/bin/env python3
"""Звіт: скільки .lisp-коду вже на повній українській проєкції `укр`.

Що міряємо
----------
`укр` — повна українська peer surface
(docs/superpowers/plans/2026-09-13-full-uk-cyrillic-surface.md). Доменні
таблиці й семантичний реєстр несуть пари `(ук …) (укр …)`: коротку й повну
форми одного об'єкта. Пара вважається **переведеною на проєкцію `укр`**, коли
обидві форми збігаються (`ук == укр`).

Дві метрики:
  * `pairs_pct`  — частка пар `ук == укр` серед усіх пар у коді (головна);
  * `files_pct`  — частка .lisp-файлів, у *коді* яких є український
                   ідентифікатор (кирилиця), тобто файл зачеплений міграцією.

Точність
--------
Пари шукаються лише в **коді**: `;`-коментарі відкидаються, але рядкові
літерали (`"…"`) зберігаються, бо значення поверхонь саме в лапках. Тому пара,
що трапилась у коментарі, не зараховується.

Поведінка
---------
Детерміновано, лише читання, без мережі. За замовчуванням друкує людський
рядок і червону анотацію GitHub (`::error::`). `--min-pairs-pct N` робить крок
жорстким: код виходу 1, поки частка < N. `--list` показує, що саме лишилось.

Коди виходу: 0 — успіх; 1 — нижче `--min-pairs-pct`; 2 — помилка аргументів.

Використання
------------
    python3 scripts/report_ukr_projection_progress.py
    python3 scripts/report_ukr_projection_progress.py --min-pairs-pct 100
    python3 scripts/report_ukr_projection_progress.py --list --top 20 --json out.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CYRILLIC = re.compile(r"[а-яїієґА-ЯЇІЄҐ]")
LATIN = re.compile(r"[A-Za-z]")
TOKEN = re.compile(r"[^\s()'\"]+")
BINARY_WORD = re.compile(r"[#:]?[01]+")


def strip_comments(text: str) -> str:
    """Прибрати `;`-коментарі, зберігши рядкові літерали й код."""
    out: list[str] = []
    i, n, in_string = 0, len(text), False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == ";":
            j = text.find("\n", i)
            if j < 0:
                break
            out.append("\n")
            i = j + 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def strip_comments_and_strings(text: str) -> str:
    """Прибрати `;`-коментарі та `"…"` рядки, лишивши тільки токени коду."""
    out: list[str] = []
    i, n, in_string = 0, len(text), False
    while i < n:
        ch = text[i]
        if in_string:
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            i += 1
            continue
        if ch == ";":
            j = text.find("\n", i)
            i = n if j < 0 else j + 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def skip_ws(text: str, i: int) -> int:
    n = len(text)
    while i < n and text[i] in " \t\r\n":
        i += 1
    return i


def read_token(text: str, i: int) -> tuple[str | None, int]:
    """Прочитати один токен поверхні: (), "…" або голий токен. None — якщо нема."""
    i = skip_ws(text, i)
    n = len(text)
    if i >= n:
        return None, i
    if text.startswith("()", i):
        return "()", i + 2
    if text[i] == '"':
        j = i + 1
        while j < n:
            if text[j] == "\\" and j + 1 < n:
                j += 2
                continue
            if text[j] == '"':
                return text[i:j + 1], j + 1
            j += 1
        return None, i
    # Апостроф НЕ є делімітером: він трапляється всередині значень поверхонь
    # (напр. `зв'язати`), тому токен читається до пробілу/дужки/лапки/коментаря.
    j = i
    while j < n and text[j] not in " \t\r\n()\";":
        j += 1
    return (text[i:j] or None), j


def iter_pairs(text: str, with_line: bool = False):
    """Пари `(ук X) (укр Y)` **у коді**; коментарі та рядки пропускаються.

    Рядок, що є *значенням* поверхні (`(ук "к")`), читається токеном; пара, що
    трапилась усередині рядка-даних, не зараховується.
    """
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == ";":
            j = text.find("\n", i)
            i = n if j < 0 else j + 1
            continue
        if ch == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if text[j] == '"':
                    j += 1
                    break
                j += 1
            i = j
            continue
        if ch == "(" and text.startswith("(ук", i) and (
                i + 3 >= n or text[i + 3] in " \t\r\n"):
            tok1, j = read_token(text, i + 3)
            if tok1 is not None and j < n and text[j] == ")":
                j += 1
            else:
                tok1 = None
            k = skip_ws(text, j) if tok1 is not None else i
            if tok1 is not None and text.startswith("(укр", k) and (
                    k + 4 >= n or text[k + 4] in " \t\r\n"):
                tok2, m = read_token(text, k + 4)
                if tok2 is not None:
                    yield (tok1, tok2, text.count("\n", 0, i) + 1) if with_line else (tok1, tok2)
                    i = m
                    continue
            i += 1
            continue
        i += 1


def latin_identifiers(code: str) -> set[str]:
    """Латинські токени коду (чисті двійкові слова не рахуються)."""
    found: set[str] = set()
    for m in TOKEN.finditer(code):
        w = m.group(0)
        if LATIN.search(w) and not BINARY_WORD.fullmatch(w):
            found.add(w)
    return found


def _norm(token: str) -> str:
    """Порівнювана форма токена: лапки та екранування зняті."""
    if token.startswith('"') and token.endswith('"') and len(token) >= 2:
        return token[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return token


@dataclass(frozen=True)
class FileReport:
    path: str
    pairs_total: int
    pairs_same: int
    ukrainian_code: bool

    @property
    def pending(self) -> int:
        return self.pairs_total - self.pairs_same


@dataclass(frozen=True)
class Progress:
    lisp_files: int = 0
    files_with_pairs: int = 0
    pairs_total: int = 0
    pairs_same: int = 0
    files_ukrainian: int = 0
    files: list[FileReport] = field(default_factory=list)

    @property
    def pairs_pct(self) -> float:
        return round(100.0 * self.pairs_same / self.pairs_total, 1) if self.pairs_total else 0.0

    @property
    def files_pct(self) -> float:
        return round(100.0 * self.files_ukrainian / self.lisp_files, 1) if self.lisp_files else 0.0

    @property
    def pairs_pending(self) -> int:
        return self.pairs_total - self.pairs_same

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("files", None)
        d["pairs_pct"] = self.pairs_pct
        d["files_pct"] = self.files_pct
        d["pairs_pending"] = self.pairs_pending
        return d


def iter_lisp_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.lisp") if ".git" not in p.parts)


def measure(root: Path) -> Progress:
    files: list[FileReport] = []
    for path in iter_lisp_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        pairs = [(a, b) for a, b in iter_pairs(text)]
        same = sum(1 for a, b in pairs if _norm(a) == _norm(b))
        has_ukrainian = bool(CYRILLIC.search(strip_comments_and_strings(text)))
        files.append(FileReport(
            path=path.relative_to(root).as_posix() if root in path.parents or path.is_relative_to(root) else str(path),
            pairs_total=len(pairs),
            pairs_same=same,
            ukrainian_code=has_ukrainian,
        ))
    return Progress(
        lisp_files=len(files),
        files_with_pairs=sum(1 for f in files if f.pairs_total),
        pairs_total=sum(f.pairs_total for f in files),
        pairs_same=sum(f.pairs_same for f in files),
        files_ukrainian=sum(1 for f in files if f.ukrainian_code),
        files=files,
    )


def render(p: Progress) -> str:
    return (
        f"УКР-ПРОЄКЦІЯ .lisp: поверхневі пари ук==укр "
        f"{p.pairs_same}/{p.pairs_total} ({p.pairs_pct}%) "
        f"у {p.files_with_pairs} файлах; "
        f".lisp-файлів з укр-поверхнею {p.files_ukrainian}/{p.lisp_files} "
        f"({p.files_pct}%)"
    )



# Output letters from the same Microsoft Ukrainian Enhanced layout as the domain test.
UKRAINIAN_KEYBOARD_OUTPUTS = set(
    "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
    "0123456789"
    "'\\-=./!\"№;%:?*()_+,₴ "
)
ROW_KEY = re.compile(r"^\s*\(([01]{1,11})\s+")


def audit_declared_ukr(root: Path) -> dict:
    """Перевіряти укр як окрему peer-поверхню; нерівність ук != укр допустима.

    Це read-only перевірка лише ОГОЛОШЕНИХ пар, не доказ усієї міграції
    викличних форм чи фізичного REPL. Усі знахідки мають шлях/рядок/ключ.
    """
    required = valid = 0
    issues: list[dict] = []
    for path in iter_lisp_files(root):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            issues.append({"file": rel, "line": 0, "key": None,
                           "reason": "symlink-not-allowed"})
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError) as exc:
            issues.append({"file": rel, "line": 0, "key": None,
                           "reason": f"unreadable:{type(exc).__name__}"})
            continue
        source_lines = source.splitlines()
        for uk, ukr, line in iter_pairs(source, with_line=True):
            if uk == ukr == "()":
                continue  # Семантичний об'єкт не має людських поверхонь.
            required += 1
            match = ROW_KEY.match(source_lines[line - 1]) if 1 <= line <= len(source_lines) else None
            key = match.group(1) if match else None
            reason = None
            if ukr == "()":
                reason = "missing-ukr"
            else:
                try:
                    value = json.loads(ukr) if ukr.startswith('"') else ukr
                    if not isinstance(value, str):
                        reason = "not-a-string"
                    else:
                        chars = sorted({ch for ch in value if ch not in UKRAINIAN_KEYBOARD_OUTPUTS}, key=ord)
                        if not value or chars:
                            reason = ("forbidden:" + ",".join(f"U+{ord(ch):04X}" for ch in chars)
                                      if chars else "empty-ukr")
                except ValueError:
                    reason = "invalid-quoted-token"
            if reason is None:
                valid += 1
            else:
                issues.append({"file": rel, "line": line, "key": key,
                               "reason": reason, "uk": uk, "ukr": ukr})
    return {"required": required, "valid": valid,
            "pct": round(100.0 * valid / required, 1) if required else 0.0,
            "issues": issues}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT), help="корінь пошуку .lisp (типово: корінь репо)")
    ap.add_argument("--json", default=None, help="записати JSON-звіт у файл")
    ap.add_argument("--min-pairs-pct", type=float, default=None,
                    help="жорсткий режим: код виходу 1, поки pairs_pct < цього порога")
    ap.add_argument("--min-ukr-pct", type=float, default=None,
                    help="жорстка перевірка наявності й допустимих символів оголошених укр")
    ap.add_argument("--list", action="store_true",
                    help="показати файли з непереведеними парами")
    ap.add_argument("--top", type=int, default=0,
                    help="обмежити --list першими N файлами (0 = усі)")
    ap.add_argument("--no-annotation", action="store_true",
                    help="не друкувати червону анотацію GitHub")
    args = ap.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print(f"::error::--root не є текою: {root}", file=sys.stderr)
        return 2

    progress = measure(root)
    declaration_audit = audit_declared_ukr(root)
    line = render(progress)
    print(line)
    if not args.no_annotation:
        print(f"::notice::{line}")

    print(f"ОГОЛОШЕНІ УКР: {declaration_audit['valid']}/{declaration_audit['required']} "
          f"({declaration_audit['pct']}%), порушень={len(declaration_audit['issues'])}; "
          "це НЕ перевірка всіх викличних форм .lisp")
    for issue in declaration_audit["issues"]:
        if not args.no_annotation:
            key = f" key={issue['key']}" if issue["key"] else ""
            print(f"::error file={issue['file']},line={issue['line']}::"
                  f"укр{key} {issue['reason']}")
    if args.list:
        pending = [f for f in progress.files if f.pending]
        pending.sort(key=lambda f: (-f.pending, f.path))
        shown = pending[:args.top] if args.top > 0 else pending
        print(f"\nФайлів із різними ук/укр (це не порушення): {len(pending)}")
        for f in shown:
            print(f"  {f.pending:5} / {f.pairs_total:5}  {f.path}")
        if args.top > 0 and len(pending) > args.top:
            print(f"  … ще {len(pending) - args.top}")

    if args.json:
        payload = progress.to_dict()
        payload["declared_ukr"] = declaration_audit
        payload["pending_files"] = [
            {"path": f.path, "pending": f.pending, "pairs_total": f.pairs_total}
            for f in sorted(progress.files, key=lambda f: f.path) if f.pending
        ]
        Path(args.json).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.min_ukr_pct is not None:
        if not 0 <= args.min_ukr_pct <= 100:
            print("::error::--min-ukr-pct має бути від 0 до 100", file=sys.stderr)
            return 2
        if (not declaration_audit["required"] or declaration_audit["issues"]
                or declaration_audit["pct"] < args.min_ukr_pct):
            print(f"::error::УКР-ОГОЛОШЕННЯ НЕ ПРОЙШЛИ: "
                  f"{declaration_audit['pct']}% < {args.min_ukr_pct}% або "
                  f"issues={len(declaration_audit['issues'])}")
            return 1
    if args.min_pairs_pct is not None and progress.pairs_pct < args.min_pairs_pct:
        print(f"::error::УКР-ПРОЄКЦІЯ НЕ ЗАВЕРШЕНА: {progress.pairs_pct}% < "
              f"порога {args.min_pairs_pct}%; лишилось {progress.pairs_pending} пар "
              f"ук != укр у {progress.files_with_pairs} файлах")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
