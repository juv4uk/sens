#!/usr/bin/env python3
"""Мігратор виконуваних голів предикатів на повну українську проєкцію.

Авторитет: ратифіковані D3/D4 таблиці, а НЕ SID8 / старий реєстр.
Не змінює цитовані дані, коментарі, рядки, фізичні .sens або Rust.
Типовий режим тільки повідомляє кандидатів; --apply вимагає окремий
чистий Git-файл lib/*.lisp. Не є доказом SENS/T5M-виконання.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from check_ukr_callsite_migration import candidate_heads, parse
from domain_tables import read_domain_table

ROOT = Path(__file__).resolve().parents[1]
NONPROGRAM = frozenset({"domains", "surface", "generated", "staged-out"})


def predicates(root: Path = ROOT) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for width in (3, 4):
        for row in read_domain_table(root / "lib/domains" / f"d{width}.lisp"):
            if not row.en or not row.en.endswith("?"):
                continue
            if not row.ukr or not row.ukr.endswith("?"):
                raise ValueError(f"{row.domain}:{row.bits}: нема ратифікованого укр-предиката")
            aliases = {row.en, row.en[:-1]}
            if row.lisp:
                aliases.update({row.lisp, row.lisp.lower()})
            for alias in aliases:
                if not alias or alias == row.ukr:
                    continue
                previous = mapping.setdefault(alias, row.ukr)
                if previous != row.ukr:
                    raise ValueError(f"неоднозначна назва {alias!r}")
    if not mapping:
        raise ValueError("порожня ратифікована карта D3/D4")
    return mapping


def rewrite_lisp(source: str, mapping: dict[str, str]) -> tuple[str, list[tuple[int, str, str]]]:
    """Використати чинний лексичний сканер викликів, не виконувати SENS у Python."""
    forms = parse(source)
    lines = [0] + [i + 1 for i, char in enumerate(source) if char == "\n"]
    edits: list[tuple[int, str, str]] = []
    for token in candidate_heads(forms):
        replacement = mapping.get(token.text)
        if replacement is None:
            continue
        at = lines[token.line - 1] + token.column - 1
        if source[at:at + len(token.text)] != token.text:
            raise ValueError(f"неправильна позиція виклику {token.line}:{token.column}")
        edits.append((at, token.text, replacement))
    if len({at for at, _, _ in edits}) != len(edits):
        raise ValueError("повторне редагування тієї ж позиції")
    result = source
    for at, old, new in sorted(edits, reverse=True):
        result = result[:at] + new + result[at + len(old):]
    if edits:
        parse(result)
    return result, edits


def selected(names: list[str], *, apply: bool) -> list[Path]:
    if apply and not names:
        raise ValueError("--apply потребує явно вибраного файла lib/*.lisp")
    result: set[Path] = set()
    for name in names or ["lib"]:
        rel = Path(name)
        if (rel.is_absolute() or not rel.parts or rel.parts[0] != "lib"
                or any(part in ("", ".", "..") for part in rel.parts)
                or any(part in NONPROGRAM for part in rel.parts[1:])):
            raise ValueError(f"поза активним lib/: {name}")
        source = ROOT / rel
        if source.is_symlink():
            raise ValueError(f"символічне посилання: {name}")
        if source.is_dir():
            if apply:
                raise ValueError("--apply не приймає каталогу: виберіть окремий файл")
            candidates = source.rglob("*.lisp")
        elif source.is_file() and source.suffix == ".lisp":
            candidates = [source]
        else:
            raise ValueError(f"немає виконуваного Lisp: {name}")
        for path in candidates:
            relative = path.relative_to(ROOT)
            if (path.is_file() and not path.is_symlink()
                    and not any(part in NONPROGRAM for part in relative.parts[1:])):
                result.add(path)
    return sorted(result)


def write_checked(path: Path, original: bytes, changed: bytes) -> None:
    rel = path.relative_to(ROOT).as_posix()
    pinned = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + rel],
                            capture_output=True, check=False)
    if pinned.returncode or pinned.stdout != original or path.read_bytes() != original:
        raise ValueError(f"{rel}: паралельні чи незакомічені зміни; перезапис заборонено")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".ukr-pred-",
                                         delete=False) as writer:
            temporary = Path(writer.name)
            writer.write(changed)
            writer.flush()
            os.fsync(writer.fileno())
        os.chmod(temporary, path.stat().st_mode)
        if path.read_bytes() != original:
            raise ValueError(f"{rel}: виявлено зміну під час публікації")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        mapping = predicates()
        files = selected(args.files, apply=args.apply)
        modified = count = 0
        for path in files:
            original = path.read_bytes()
            result, edits = rewrite_lisp(original.decode("utf-8", "strict"), mapping)
            if edits:
                modified += 1
                count += len(edits)
                print(f"{path.relative_to(ROOT)}: {len(edits)} точних укр-викликів")
                if args.apply:
                    write_checked(path, original, result.encode("utf-8"))
        print(f"УКР_ПРЕДИКАТИ: файлів={len(files)} кандидатів={modified} викликів={count} "
              f"запис={args.apply}; семантичний_оракул=НЕ_ПЕРЕВІРЕНО")
        return 0
    except (ValueError, OSError, UnicodeError, RuntimeError) as error:
        print(f"ПОМИЛКА УКР_ПРЕДИКАТИ: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
