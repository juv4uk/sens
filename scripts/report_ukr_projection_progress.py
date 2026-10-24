#!/usr/bin/env python3
"""Єдиний показник міграції: повністю українські файли .lisp.

Файл зараховується, якщо КОЖЕН символ його повного вмісту можна набрати
українською розкладкою клавіатури. Коментарі, літерали, цитовані дані,
пробіли та переводи рядків перевіряються так само, як виконуваний код.
Історичні каталоги входять до знаменника. Вкладені `.worktrees` є окремими
живими клонами/гілками, а не файлами цього checkout, тому не входять до метрики.
Неправильний UTF-8, недоступний файл і символ поза розкладкою не
зараховуються. Порожні файли і файли лише з пробільними символами не є завершеними програмами.
Ця метрика не стверджує семантичної правильності чи працездатності SENS.

Використання:
    python3 scripts/report_ukr_projection_progress.py
    python3 scripts/report_ukr_projection_progress.py --list --top 20
    python3 scripts/report_ukr_projection_progress.py --json результат.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Ті самі символи Microsoft Ukrainian Enhanced, що й у чинних правилах
# проєкції доменів. Enter, Tab і CR/LF дозволені як клавіші керування.
UKRAINIAN_KEYBOARD_OUTPUTS = set(
    "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
    "0123456789"
    "'\\-=./!\"№;%:?*()_+,₴ "
)
KEYBOARD_WHITESPACE = set("\t\r\n")
ALLOWED = UKRAINIAN_KEYBOARD_OUTPUTS | KEYBOARD_WHITESPACE


@dataclass(frozen=True)
class Unfinished:
    path: str
    reason: str


@dataclass(frozen=True)
class Progress:
    total_lisp_files: int
    fully_ukrainian_files: int
    pending: tuple[Unfinished, ...]

    @property
    def percent(self) -> float:
        return round(self.fully_ukrainian_files * 100 / self.total_lisp_files, 1) if self.total_lisp_files else 0.0

    def to_dict(self) -> dict:
        return {
            "total_lisp_files": self.total_lisp_files,
            "fully_ukrainian_files": self.fully_ukrainian_files,
            "percent": self.percent,
        }


def iter_lisp_files(root: Path) -> list[Path]:
    """Файли цього дерева; історію рахуємо, вкладені робочі дерева — ні."""
    return sorted(
        (path for path in root.rglob("*.lisp")
         if not ({".git", ".worktrees"} & set(path.relative_to(root).parts))),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def examine_file(path: Path) -> str | None:
    """None — усі символи доступні; інакше діагноз першої проблеми."""
    if path.is_symlink():
        return "символічне посилання (не є самостійним вмістом файла)"
    try:
        source = path.read_bytes().decode("utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        return f"непрочитаний файл або неправильний UTF-8: {type(exc).__name__}"
    if not source.strip():
        return "порожній файл або лише пробіли"
    for offset, char in enumerate(source):
        if char not in ALLOWED:
            line = source.count("\n", 0, offset) + 1
            column = offset - source.rfind("\n", 0, offset)
            return f"{line}:{column}: U+{ord(char):04X} {char!r}"
    return None



@dataclass(frozen=True)
class SourceProjection:
    total_source_files: int
    fully_projected_source_files: int
    pending: tuple[Unfinished, ...]
    excluded_nonprogram_files: int

    @property
    def percent(self) -> float:
        return (
            round(self.fully_projected_source_files * 100 / self.total_source_files, 1)
            if self.total_source_files else 0.0
        )

    def to_dict(self) -> dict:
        return {
            "total_source_files": self.total_source_files,
            "fully_projected_source_files": self.fully_projected_source_files,
            "percent": self.percent,
            "excluded_nonprogram_files": self.excluded_nonprogram_files,
        }


@dataclass(frozen=True)
class LispToken:
    kind: str
    value: str
    line: int
    column: int


@dataclass(frozen=True)
class LispAtom:
    token: LispToken


@dataclass(frozen=True)
class LispOpaque:
    token: LispToken


@dataclass(frozen=True)
class LispQuoted:
    value: object


@dataclass(frozen=True)
class LispForm:
    items: tuple[object, ...]
    line: int
    column: int


LATIN_IDENTIFIER = re.compile(r"[A-Za-z]")
RAW_BINARY_HEAD = re.compile(r"[01]{3,11}\Z")
NONPROGRAM_LIB_PATHS = (
    "lib/domains/",
    "lib/generated/",
)
NONPROGRAM_LIB_FILES = frozenset({
    "lib/machine/encoding/coverage.lisp",
})
# Каталоги, чиї `.lisp` — ДАНІ, а не виконувані програми (таблиці, реєстри,
# машинні дані, контракти, знання, документація, свідки, фізичні/до-міграційні
# приклади, Rust-крейти). Див. також NONPROGRAM_LIB_PATHS/FILES вище.
NONPROGRAM_TREE_PATHS = (
    "contracts/",
    "knowledge/",
    "docs/",
    "tests/",
    "fixtures/",
    "examples/binary",
    "examples/migrated/",
    "crates/",
)


def _advance_position(fragment: str, line: int, column: int) -> tuple[int, int]:
    newlines = fragment.count("\n")
    if newlines:
        return line + newlines, len(fragment.rsplit("\n", 1)[-1]) + 1
    return line, column + len(fragment)


def tokenize_lisp(source: str) -> list[LispToken]:
    """Tokenize enough Lisp structure for a source-only projection census."""
    tokens: list[LispToken] = []
    i, line, column, size = 0, 1, 1, len(source)
    while i < size:
        char = source[i]
        if char.isspace():
            line, column = _advance_position(char, line, column)
            i += 1
            continue
        if source.startswith("#|", i):
            start, depth = i, 1
            i += 2
            while i < size and depth:
                if source.startswith("#|", i):
                    depth += 1
                    i += 2
                elif source.startswith("|#", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise ValueError(f"{line}:{column}: незакритий блоковий коментар")
            fragment = source[start:i]
            line, column = _advance_position(fragment, line, column)
            continue
        if char == ";":
            start = i
            while i < size and source[i] != "\n":
                i += 1
            fragment = source[start:i]
            line, column = _advance_position(fragment, line, column)
            continue
        start, start_line, start_column = i, line, column
        if char == '"':
            i += 1
            while i < size:
                if source[i] == "\\":
                    i += 2
                elif source[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise ValueError(f"{start_line}:{start_column}: незакритий рядок")
            value = source[start:i]
            tokens.append(LispToken("STRING", value, start_line, start_column))
        elif char == "(":
            i += 1
            tokens.append(LispToken("LPAREN", char, start_line, start_column))
        elif char == ")":
            i += 1
            tokens.append(LispToken("RPAREN", char, start_line, start_column))
        elif char == "'" and (i == 0 or source[i - 1].isspace() or source[i - 1] in "();"):
            i += 1
            tokens.append(LispToken("QUOTE", char, start_line, start_column))
        else:
            i += 1
            while i < size and not source[i].isspace() and source[i] not in '();"':
                i += 1
            value = source[start:i]
            tokens.append(LispToken("ATOM", value, start_line, start_column))
        fragment = source[start:i]
        line, column = _advance_position(fragment, start_line, start_column)
    return tokens


def parse_lisp_tokens(tokens: list[LispToken]) -> list[object]:
    """Parse list boundaries and quote forms; no evaluation or name resolution."""
    def one(index: int) -> tuple[object, int]:
        if index >= len(tokens):
            raise ValueError("неочікуваний кінець Lisp-файла")
        token = tokens[index]
        if token.kind == "STRING":
            return LispOpaque(token), index + 1
        if token.kind == "ATOM":
            return LispAtom(token), index + 1
        if token.kind == "QUOTE":
            quoted, after = one(index + 1)
            return LispQuoted(quoted), after
        if token.kind == "RPAREN":
            raise ValueError(f"{token.line}:{token.column}: зайва закривальна дужка")
        if token.kind == "LPAREN":
            items: list[object] = []
            index += 1
            while index < len(tokens) and tokens[index].kind != "RPAREN":
                child, index = one(index)
                items.append(child)
            if index >= len(tokens):
                raise ValueError(f"{token.line}:{token.column}: незакрита форма")
            return LispForm(tuple(items), token.line, token.column), index + 1
        raise ValueError(f"{token.line}:{token.column}: невідомий токен {token.kind}")

    forms: list[object] = []
    index = 0
    while index < len(tokens):
        node, index = one(index)
        forms.append(node)
    return forms


def _atom_value(node: object) -> str | None:
    return node.token.value if isinstance(node, LispAtom) else None


def _projection_reasons(source: str) -> list[str]:
    """Find every English callable, binder or DEFINE alias; exclude quoted data."""
    forms = parse_lisp_tokens(tokenize_lisp(source))
    reasons: list[str] = []

    def add(token: LispToken, kind: str, value: str) -> None:
        reasons.append(f"{token.line}:{token.column}: {kind} {value!r}")

    def visit(node: object) -> None:
        if isinstance(node, (LispQuoted, LispOpaque)):
            return
        if isinstance(node, LispAtom):
            # Вільний ідентифікатор у тілі є виконуваним посиланням,
            # навіть якщо він не стоїть на місці викличної голови.
            if LATIN_IDENTIFIER.search(node.token.value):
                add(node.token, "англомовне посилання на значення", node.token.value)
            return
        if not isinstance(node, LispForm) or not node.items:
            return
        head = node.items[0]
        head_value = _atom_value(head)
        if head_value is None:
            for child in node.items:
                visit(child)
            return

        # The contents of SENS's quote form are data, not executable call heads.
        if head_value == "як-є":
            return

        head_token = head.token
        if RAW_BINARY_HEAD.fullmatch(head_value):
            add(head_token, "сира бінарна голова", head_value)
        elif LATIN_IDENTIFIER.search(head_value):
            add(head_token, "англомовна виклична голова", head_value)

        if head_value == "визначити" and len(node.items) >= 2:
            target = node.items[1]
            target_value = _atom_value(target)
            if target_value and LATIN_IDENTIFIER.search(target_value):
                # Назва визначення — зв'язування, а не звернення до значення.
                add(target.token, "англомовна назва визначення", target_value)
            for child in node.items[2:]:
                visit(child)
            return

        if head_value == "функція" and len(node.items) >= 2:
            formals = node.items[1]
            if isinstance(formals, LispForm):
                for formal in formals.items:
                    formal_value = _atom_value(formal)
                    if formal_value and LATIN_IDENTIFIER.search(formal_value):
                        add(formal.token, "англомовний локальний параметр", formal_value)
            elif isinstance(formals, LispAtom):
                # Lisp allows a single bare rest parameter: (функція args ...).
                # This is a binding, not quoted data or an ignorable value.
                formal_value = _atom_value(formals)
                if formal_value and LATIN_IDENTIFIER.search(formal_value):
                    add(formals.token, "англомовний локальний параметр", formal_value)
            for child in node.items[2:]:
                visit(child)
            return

        for child in node.items[1:]:
            visit(child)

    for form in forms:
        visit(form)
    return reasons


def _contains_source_definitions(path: Path) -> bool:
    """A surface file with top-level DEFINE is a program, not a projection table.

    Only inspect syntax here: executable semantics belong to native SENS.
    Invalid or unreadable source stays in the audit instead of disappearing.
    """
    try:
        forms = parse_lisp_tokens(tokenize_lisp(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, ValueError):
        return True
    return any(
        isinstance(form, LispForm)
        and bool(form.items)
        and _atom_value(form.items[0]) in {"визначити", "define"}
        for form in forms
    )


def iter_projectable_source_files(root: Path) -> tuple[list[Path], int]:
    """Active authored library programs; semantic tables and generated inventory are reported separately."""
    # Першопричина: раніше перелік брався лише з `lib/`, тож виконувані
    # `scripts/*.lisp` і кореневі `.lisp` не входили у знаменник узагалі —
    # їхню міграцію метрика не бачила. Тепер набір виводиться з ДЕРЕВА,
    # а дані/таблиці/фізичні свідки виключені явними коренями.
    all_files = sorted(
        (
            path
            for path in root.rglob("*.lisp")
            if path.is_file()
            and not path.is_symlink()
            and ".git" not in path.parts
            and not any(
                path.relative_to(root).as_posix().startswith(prefix)
                for prefix in NONPROGRAM_TREE_PATHS
            )
        ),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    if not all_files:
        return [], 0
    selected: list[Path] = []
    excluded = 0
    for path in all_files:
        relative = path.relative_to(root).as_posix()
        # Виконувані DEFINE у lib/surface — не каталог. Раніше всі вони
        # випадали зі знаменника, приховуючи реальні незавершені програми.
        if relative.startswith("lib/surface/") and not _contains_source_definitions(path):
            excluded += 1
            continue
        if relative in NONPROGRAM_LIB_FILES or any(
            relative.startswith(prefix) for prefix in NONPROGRAM_LIB_PATHS
        ):
            excluded += 1
            continue

        # Файл лише з коментарів (також вкладених #|...|#) не містить
        # виконуваних форм і не збільшує чисельник «проєктованих програм».
        # Пошкоджений коментар / UTF-8 залишається в аудиті як помилка.
        try:
            has_forms = bool(tokenize_lisp(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, ValueError):
            has_forms = True
        if not has_forms:
            excluded += 1
            continue

        # ISA-каталог — дані про процесор, НЕ виконуваний Lisp.
        # Не додаємо його латинські mnemonic/extension поля до боргу
        # українських викликів. Доводимо саме AST-формою документа, а не
        # сліпо виключаємо цілий каталог: DEFINE та зіпсовані файли
        # повинні залишатися в аудиті.
        if relative.startswith("lib/machine/isa/"):
            try:
                forms = parse_lisp_tokens(tokenize_lisp(
                    path.read_text(encoding="utf-8")
                ))
            except (OSError, UnicodeError, ValueError):
                selected.append(path)
                continue
            if (len(forms) == 1
                and isinstance(forms[0], LispForm)
                and bool(forms[0].items)
                and _atom_value(forms[0].items[0]) == "isa-catalogue-1"):
                excluded += 1
                continue
        selected.append(path)
    return selected, excluded


def examine_source_projection(path: Path) -> str | None:
    try:
        source = path.read_bytes().decode("utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        return f"непрочитаний файл або неправильний UTF-8: {type(exc).__name__}"
    if not source.strip():
        return "порожній файл або лише пробіли"
    try:
        reasons = _projection_reasons(source)
    except ValueError as exc:
        return str(exc)
    return reasons[0] if reasons else None


def measure_source_projection(root: Path) -> SourceProjection:
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    files, excluded = iter_projectable_source_files(root)
    pending = []
    for path in files:
        reason = examine_source_projection(path)
        if reason is not None:
            pending.append(Unfinished(path.relative_to(root).as_posix(), reason))
    return SourceProjection(
        total_source_files=len(files),
        fully_projected_source_files=len(files) - len(pending),
        pending=tuple(pending),
        excluded_nonprogram_files=excluded,
    )


def render_source_projection(progress: SourceProjection) -> str:
    return (
        "УКР-ПРОЄКЦІЯ: виконувані назви, голови та параметри в активних .lisp-програмах (дерево, не лише lib) — "
        f"{progress.fully_projected_source_files}/{progress.total_source_files} "
        f"({progress.percent:.1f}%)"
    )


def measure(root: Path) -> Progress:
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    files = iter_lisp_files(root)
    pending = []
    for path in files:
        reason = examine_file(path)
        if reason is not None:
            pending.append(Unfinished(path.relative_to(root).as_posix(), reason))
    return Progress(
        total_lisp_files=len(files),
        fully_ukrainian_files=len(files) - len(pending),
        pending=tuple(pending),
    )


def render(progress: Progress) -> str:
    return (f"УКР-ПРОЄКЦІЯ: повністю українські файли .lisp — "
            f"{progress.fully_ukrainian_files}/{progress.total_lisp_files} "
            f"({progress.percent:.1f}%)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="коренева тека всіх .lisp")
    parser.add_argument("--json", type=Path, default=None,
                        help="записати лише три показники у JSON")
    parser.add_argument("--list", action="store_true",
                        help="перелічити файли з недоступними символами")
    parser.add_argument("--projection-list", action="store_true",
                        help="перелічити активні lib-файли з непроєктованими виконуваними іменами")
    parser.add_argument("--top", type=int, default=0,
                        help="кількість рядків у --list, 0 означає всі")
    parser.add_argument("--no-annotation", action="store_true",
                        help="не створювати інформаційну позначку GitHub")
    args = parser.parse_args(argv)

    if not args.root.is_dir():
        print(f"::error::--root не є текою: {args.root}", file=sys.stderr)
        return 2
    if args.top < 0:
        parser.error("--top має бути невід'ємним")

    progress = measure(args.root)
    source_projection = measure_source_projection(args.root)
    keyboard_message = render(progress)
    source_message = render_source_projection(source_projection)
    print(keyboard_message)
    print(source_message)
    if not args.no_annotation and os.getenv("GITHUB_ACTIONS") == "true":
        print(f"::notice::{keyboard_message}")
        print(f"::notice::{source_message}")

    if args.list:
        pending = progress.pending
        shown = pending[:args.top] if args.top else pending
        print("УКР-ПРОЄКЦІЯ — незавершені файли:")
        for item in shown:
            print(f"{item.path}: {item.reason}")
        if args.top and len(pending) > args.top:
            print(f"… ще {len(pending) - args.top}")

    if args.projection_list:
        pending = source_projection.pending
        shown = pending[:args.top] if args.top else pending
        print("УКР-ПРОЄКЦІЯ — невиконані активні lib-файли:")
        for item in shown:
            print(f"{item.path}: {item.reason}")
        if args.top and len(pending) > args.top:
            print(f"… ще {len(pending) - args.top}")

    if args.json is not None:
        payload = progress.to_dict()
        payload["source_projection"] = source_projection.to_dict()
        args.json.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
