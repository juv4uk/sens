#!/usr/bin/env python3
"""Звіт про українську проєкцію SENS: окремо словник і активні виклики.

Основний показник прогресу — `executable_ukr.files_pct`: частка активних
виконуваних .lisp-файлів, усі розпізнані викличні голови яких належать
українській клавіатурі і, якщо це ім'я ратифікованого домену, повній
колонці «укр». Незчитаний файл є незавершеним. Історичні тексти, цитовані
дані, таблиці доменів та записи без викличних голів не збільшують знаменник.
Це статичний показник, НЕ доказ SENS eval, семантичної еквівалентності чи T5M.

Додаткова історична телеметрія:
  * `pairs_pct`  — буквальна однаковість `(ук X)` і `(укр Y)`; різні
                   коректні короткі/повні назви НЕ є проблемою міграції;
  * `files_pct`  — частка всіх .lisp із хоча б одним кириличним токеном
                   поза рядками й коментарями; НЕ частка завершених файлів.

Точність
--------
Пари шукаються лише в **коді**: `;`-коментарі відкидаються, але рядкові
літерали (`"…"`) зберігаються, бо значення поверхонь саме в лапках. Тому пара,
що трапилась у коментарі, не зараховується.

Поведінка
---------
Детерміновано, лише читання, без мережі. За замовчуванням друкує людський
рядок і інформаційну анотацію GitHub (`::notice::`). `--min-pairs-pct N` робить крок
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
import importlib.util
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Спільний аналізатор викликів доступний і у CLI, і при імпорті тестами.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

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
    active_executable_files: int = 0
    active_files_without_latin_heads: int = 0
    active_ukr_head_sites: int = 0
    active_latin_head_sites: int = 0
    active_encoded_head_sites: int = 0
    active_unreadable_files: int = 0

    @property
    def pairs_pct(self) -> float:
        return round(100.0 * self.pairs_same / self.pairs_total, 1) if self.pairs_total else 0.0

    @property
    def files_pct(self) -> float:
        return round(100.0 * self.files_ukrainian / self.lisp_files, 1) if self.lisp_files else 0.0

    @property
    def pairs_pending(self) -> int:
        return self.pairs_total - self.pairs_same

    @property
    def active_files_pct(self) -> float:
        return (round(100.0 * self.active_files_without_latin_heads /
                      self.active_executable_files, 1)
                if self.active_executable_files else 0.0)

    @property
    def active_heads_pct(self) -> float:
        total = self.active_ukr_head_sites + self.active_latin_head_sites
        return round(100.0 * self.active_ukr_head_sites / total, 1) if total else 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("files", None)
        d["pairs_pct"] = self.pairs_pct
        d["files_pct"] = self.files_pct
        d["pairs_pending"] = self.pairs_pending
        d["active_files_pct"] = self.active_files_pct
        d["active_heads_pct"] = self.active_heads_pct
        return d


def iter_lisp_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.lisp") if ".git" not in p.parts)


def _callsite_audit():
    """Reuse the existing source parser; do not invent a second lexical oracle."""
    name = "_sens_ukr_callsite_report"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).with_name("check_ukr_callsite_migration.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("Немає чинного аудитора викличних голів")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def measure(root: Path) -> Progress:
    files: list[FileReport] = []
    audit = _callsite_audit()
    live_count = live_clean = live_ukr = live_latin = live_encoded = live_bad = 0
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
        rel = path.relative_to(root)
        archival = (not rel.parts or rel.parts[0] not in audit.LIVE_SOURCE_DIRS
                    or 'tests' in rel.parts or 'fixtures' in rel.parts
                    or (rel.parts[0] == 'examples' and 'history' in rel.parts))
        if archival or audit.excluded_metadata(rel):
            continue
        live_count += 1
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            live_bad += 1
            continue
        try:
            heads = list(audit.candidate_heads(audit.parse(text)))
        except (audit.SourceError, RecursionError, UnicodeError):
            live_bad += 1
            continue
        latin = sum(bool(audit.LATIN.search(head.text)) for head in heads)
        encoded = sum(bool(audit.ENCODED_HEAD.fullmatch(head.text)) for head in heads)
        ukr = sum(bool(audit.UKRAINIAN.search(head.text)) for head in heads)
        live_latin += latin
        live_encoded += encoded
        live_ukr += ukr
        # Purely lexical completion, NOT proof of executable SENS semantics.
        if ukr and not latin and not encoded:
            live_clean += 1
    return Progress(
        lisp_files=len(files),
        files_with_pairs=sum(1 for f in files if f.pairs_total),
        pairs_total=sum(f.pairs_total for f in files),
        pairs_same=sum(f.pairs_same for f in files),
        files_ukrainian=sum(1 for f in files if f.ukrainian_code),
        files=files,
        active_executable_files=live_count,
        active_files_without_latin_heads=live_clean,
        active_ukr_head_sites=live_ukr,
        active_latin_head_sites=live_latin,
        active_encoded_head_sites=live_encoded,
        active_unreadable_files=live_bad,
    )


def audit_executable_ukr_files(root: Path) -> dict:
    """Статична файлова метрика за викличними головами, а не за згадкою кирилиці.

    Використовує ТУ САМУ структуру reader/heads, що й чинний
    check_ukr_callsite_migration.py; не додає власного Lisp-інтерпретатора.
    Незчитане активне джерело не може отримати статус повної проєкції.
    """
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import check_ukr_callsite_migration as calls

    root = root.resolve()
    index, authority = calls.peer_index(root)
    roles = calls.peer_roles(root)
    eligible = converted = unclassified = without_heads = excluded = 0
    pending_files: list[dict] = []
    for path in iter_lisp_files(root):
        rel = path.relative_to(root)
        if (not rel.parts or rel.parts[0] not in calls.LIVE_SOURCE_DIRS
                or "tests" in rel.parts or "fixtures" in rel.parts
                or (rel.parts[0] == "examples" and "history" in rel.parts)
                or calls.excluded_metadata(rel)):
            excluded += 1
            continue

        reason = None
        try:
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise calls.SourceError("symlink/out-of-root source")
            forms = calls.parse(path.read_text(encoding="utf-8"))
            heads = list(calls.candidate_heads(forms))
            if not heads:
                without_heads += 1
                continue
            eligible += 1
            for head in heads:
                name = head.text
                spelling = name.casefold()
                identities = index.get(spelling, ())
                kinds = roles.get(spelling, set())
                if calls.ENCODED_HEAD.fullmatch(name) or calls.BIT_WORD.fullmatch(name):
                    reason = "encoded-or-bit-head"
                elif calls.LATIN.search(name):
                    reason = "latin-call-head"
                elif not calls.UKRAINIAN.search(name) or any(
                        char not in UKRAINIAN_KEYBOARD_OUTPUTS for char in name):
                    reason = "non-ukrainian-keyboard-head"
                elif len(identities) > 1:
                    reason = "ambiguous-ratified-name"
                elif "ук" in kinds and "укр" not in kinds:
                    reason = "compact-instead-of-full-ukr"
                if reason:
                    break
        except (UnicodeError, OSError, calls.SourceError, RecursionError) as exc:
            eligible += 1
            unclassified += 1
            reason = "unreadable-or-unparsed: " + str(exc)
        if reason:
            pending_files.append({"path": rel.as_posix(), "reason": reason})
        else:
            converted += 1

    return {
        "eligible_files": eligible,
        "full_ukr_files": converted,
        "pending_files_count": eligible - converted,
        "files_pct": round(100.0 * converted / eligible, 1) if eligible else 0.0,
        "unclassified_files": unclassified,
        "without_executable_heads_excluded": without_heads,
        "archives_and_metadata_excluded": excluded,
        "authority_rows": authority["domain_rows"],
        "pending_files": pending_files,
        "evidence": "static call-head classification, not SENS runtime parity",
    }


def render(p: Progress, executable_ukr: dict | None = None) -> str:
    legacy = (
        f"УКР-ПРОЄКЦІЯ .lisp: поверхневі пари ук==укр "
        f"{p.pairs_same}/{p.pairs_total} ({p.pairs_pct}%) "
        f"у {p.files_with_pairs} файлах; "
        f".lisp-файлів з укр-поверхнею {p.files_ukrainian}/{p.lisp_files} "
        f"({p.files_pct}% — лише наявність кирилиці, НЕ завершення); "
        f"активні .lisp без латинських викличних голів "
        f"{p.active_files_without_latin_heads}/{p.active_executable_files} "
        f"({p.active_files_pct}%, лексично); "
        f"активні українські викличні голови "
        f"{p.active_ukr_head_sites}/"
        f"{p.active_ukr_head_sites + p.active_latin_head_sites} "
        f"({p.active_heads_pct}%); "
        f"сирих кодів={p.active_encoded_head_sites}, "
        f"непрочитаних={p.active_unreadable_files}"
    )
    if executable_ukr is None:
        return legacy
    return (f"УКР-ПРОГРЕС виконуваних .lisp: "
            f"{executable_ukr['full_ukr_files']}/{executable_ukr['eligible_files']} "
            f"({executable_ukr['files_pct']}%) повністю укр за викличними "
            f"головами; незчитаних={executable_ukr['unclassified_files']}; "
            + legacy)



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
    executable_ukr = audit_executable_ukr_files(root)
    line = render(progress, executable_ukr)
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

        incomplete = executable_ukr["pending_files"]
        print(f"\nАктивних виконуваних .lisp ще не на повній укр: {len(incomplete)}")
        shown_ukr = incomplete[:args.top] if args.top > 0 else incomplete
        for item in shown_ukr:
            print(f"  {item['path']}: {item['reason']}")
        if args.top > 0 and len(incomplete) > args.top:
            print(f"  … ще {len(incomplete) - args.top}")

    if args.json:
        payload = progress.to_dict()
        payload["declared_ukr"] = declaration_audit
        payload["executable_ukr"] = executable_ukr
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
