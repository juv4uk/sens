#!/usr/bin/env python3
"""Детермінований аудит і лише явно обґрунтована міграція ук/укр/sym D1–D11.

Типова поведінка — read-only dry-run. D7 береться лише з ратифікованої
knowledge/d7-keyboard-v2-ratified.json; інші значення НЕ транслітеруються:
для виправлення потрібен явний authority-manifest за координатою і колонкою.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path

COLUMNS = ("ук", "укр", "sym")
TOKEN = r'(?:\(\)|"(?:\\.|[^"\\])*"|[^()\s]+)'
ROW = re.compile(
    r"^(?P<a>\s*\([01]{1,11}\s+\(ук\s+)"
    + rf"(?P<uk>{TOKEN})(?P<b>\)\s+\(укр\s+)"
    + rf"(?P<ukr>{TOKEN})(?P<c>\)\s+\(san\s+)"
    + rf"(?P<san>{TOKEN})(?P<d>\)\s+\(en\s+)"
    + rf"(?P<en>{TOKEN})(?P<e>\)\s+\(LISP\s+)"
    + rf"(?P<lisp>{TOKEN})(?P<f>\)\s+\(sym\s+)"
    + rf"(?P<sym>{TOKEN})(?P<z>\)\)\s*)$"
)
KEY = re.compile(r"^\s*\(([01]{1,11})\s+")
ALLOWED = set(
    "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
    "0123456789"
    "'\\-=./!\"№;%:?*()_+,₴ "
)


@dataclass(frozen=True)
class Change:
    file: str
    bits: str
    column: str
    before: str
    after: str | None
    authority: str

    @property
    def coordinate(self) -> str:
        return f"D{len(self.bits)}:{self.bits}"


def displayed(token: str, width: int) -> str:
    if token == "()":
        return ""
    if token.startswith('"'):
        escaped_controls = "".join(
            f"\\u{ord(ch):04x}" if ord(ch) < 0x20 else ch for ch in token
        )
        value = json.loads(escaped_controls)
    else:
        value = token
    if width == 7 and re.fullmatch(r"\\x[0-9a-fA-F]{2}", value):
        return chr(int(value[2:], 16))
    return value


def keyboard_valid(token: str, width: int) -> bool:
    return all(
        (not char.isprintable()) or char in ALLOWED
        for char in displayed(token, width)
    )


def d7_authority(root: Path) -> dict[str, str]:
    path = root / "knowledge/d7-keyboard-v2-ratified.json"
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"D7 authority поза --root або відсутня: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("status") != "owner-ratified" or data.get("width") != 7:
        raise ValueError(f"відсутня ратифікація D7: {path}")
    entries = data["table"]
    authority: dict[str, str] = {}
    for entry in entries:
        bits, value = entry["bits"], entry["uk"]
        if not re.fullmatch(r"[01]{7}", bits) or bits in authority:
            raise ValueError(f"неоднозначний D7 код: {bits}")
        if not value.isprintable():
            token = "()"
        elif len(value) == 1 and unicodedata.category(value).startswith("L"):
            # Domain tables write alphabetic projection glyphs as bare Lisp
            # symbols; punctuation and digit glyphs remain quoted data.
            token = value
        else:
            token = json.dumps(value, ensure_ascii=False)
        if not keyboard_valid(token, 7):
            raise ValueError(f"неприпустимий ратифікований D7 символ: {bits}")
        authority[bits] = token
    if len(authority) != 128:
        raise ValueError("D7 authority має містити рівно 128 координат")
    return authority


def load_manifest(path: Path | None) -> dict[tuple[str, str, str, str], tuple[str, str]]:
    if path is None:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema") != "ukrainian-projection-authority/1":
        raise ValueError("невідомий формат authority-manifest")
    out: dict[tuple[str, str, str, str], tuple[str, str]] = {}
    # One authority resolution per exact coordinate/column, even across old spellings.
    claimed_cells: set[tuple[str, str, str]] = set()
    for item in raw["replacements"]:
        domain, bits, col = item["domain"], item["bits"], item["column"]
        before, after, authority = item["before"], item["after"], item["authority"]
        if (domain not in {f"D{i}" for i in range(1, 12)}
                or not re.fullmatch(rf"[01]{{{int(domain[1:])}}}", bits)
                or col not in COLUMNS or not isinstance(authority, str)
                or not authority.strip() or not isinstance(before, str)
                or not isinstance(after, str)):
            raise ValueError(f"неприпустима відповідність: {item!r}")
        if not keyboard_valid(after, len(bits)):
            raise ValueError(f"ціль поза українською клавіатурою: {item!r}")
        key = (domain, bits, col, before)
        cell = (domain, bits, col)
        if cell in claimed_cells:
            raise ValueError(f"неоднозначна/повторна відповідність: {cell}")
        claimed_cells.add(cell)
        out[key] = (after, authority)
    return out


def audit(
    root: Path, manifest: dict[tuple[str, str, str, str], tuple[str, str]] | None = None
) -> tuple[list[Change], dict[Path, tuple[bytes, bytes]]]:
    """Повна попередня перевірка; жодних записів до повернення результату."""
    root = root.resolve()
    manifest = manifest or {}
    d7 = d7_authority(root)
    changes: list[Change] = []
    plans: dict[Path, tuple[bytes, bytes]] = {}
    observed: dict[tuple[str, str, str], str] = {}
    for width in range(1, 12):
        path = root / "lib/domains" / f"d{width}.lisp"
        if (not path.is_file() or path.is_symlink()
                or not path.resolve().is_relative_to(root)):
            raise ValueError(f"{path}: файл відсутній, є посиланням або виходить за --root")
        before_bytes = path.read_bytes()
        source = before_bytes.decode("utf-8")
        lines: list[str] = []
        seen_bits: set[str] = set()
        for number, line in enumerate(source.splitlines(keepends=True), 1):
            body = line.rstrip("\r\n")
            suffix = line[len(body):]
            matched = ROW.fullmatch(body)
            if not matched:
                if KEY.match(body):
                    raise ValueError(f"{path}:{number} неканонічний рядок домену")
                lines.append(line)
                continue
            value = matched.groupdict()
            bits = KEY.match(body).group(1)
            if len(bits) != width or bits in seen_bits:
                raise ValueError(f"{path}:{number} неправильний/повторний ключ")
            seen_bits.add(bits)
            replacements: dict[str, str] = {}
            for column, group in (("ук", "uk"), ("укр", "ukr"), ("sym", "sym")):
                old = value[group]
                observed[(f"D{width}", bits, column)] = old
                authority_token = d7[bits] if width == 7 else None
                selection = manifest.get((f"D{width}", bits, column, old))
                if width == 7:
                    if selection and selection[0] != authority_token:
                        raise ValueError(f"D7 authority-conflict: {bits}/{column}")
                    authority = "knowledge/d7-keyboard-v2-ratified.json"
                    if old == authority_token:
                        target = old
                    elif not keyboard_valid(old, width):
                        target = authority_token
                    else:
                        # Чинний друкований знак може бути іншою людською
                        # проєкцією. Його зміна потребує рішення власника.
                        target = None
                        authority += " (потрібне уточнення власника)"
                elif not keyboard_valid(old, width):
                    target = selection[0] if selection else None
                    authority = selection[1] if selection else "НЕОДНОЗНАЧНО"
                else:
                    target = old
                    authority = ""
                if target != old:
                    changes.append(Change(
                        str(path.relative_to(root)), bits, column, old, target, authority
                    ))
                replacements[group] = target if target is not None else old
            new_body = (
                value["a"] + replacements["uk"] + value["b"]
                + replacements["ukr"] + value["c"] + value["san"]
                + value["d"] + value["en"] + value["e"] + value["lisp"]
                + value["f"] + replacements["sym"] + value["z"]
            )
            if not ROW.fullmatch(new_body):
                raise ValueError(f"{path}:{number} зміна порушила форму таблиці")
            check = ROW.fullmatch(new_body)
            for invariant in ("a", "b", "c", "san", "d", "en", "e", "lisp", "f", "z"):
                if value[invariant] != check.group(invariant):
                    raise ValueError(f"{path}:{number} порушено сторонню колонку {invariant}")
            lines.append(new_body + suffix)
        new_bytes = "".join(lines).encode("utf-8")
        if before_bytes != new_bytes:
            plans[path] = (before_bytes, new_bytes)
    for (domain, bits, column, previous), (after, _authority) in manifest.items():
        current = observed.get((domain, bits, column))
        if current not in (previous, after):
            raise ValueError(f"застаріла/невизначена відповідність {domain}:{bits}/{column}")
    return changes, plans


def execute(root: Path, mapping: Path | None = None, apply: bool = False) -> list[Change]:
    authority = load_manifest(mapping)
    changes, plans = audit(root, authority)
    for item in changes:
        print(
            f"{item.file} {item.coordinate} column={item.column} "
            f"before={item.before!r} after={item.after!r} authority={item.authority}"
        )
    # D7 — лише аудит: навіть за порушення розкладки exact W7
    # не можна переписувати людський символ без рішення власника.
    # Перевіряємо ДО першого запису, також коли інші домени схвалені.
    d7_findings = [c for c in changes if len(c.bits) == 7]
    if d7_findings and apply:
        raise ValueError(
            f"D7 лише dry-run; {len(d7_findings)} проєкцій потребують "
            "окремого рішення власника; нічого не записано"
        )
    unresolved = [c for c in changes if c.after is None]
    if unresolved and apply:
        raise ValueError(f"{len(unresolved)} неоднозначних замін; нічого не записано")
    if apply:
        # Перевірка усіх вхідних байтів до першої зміни.
        for path, (before, _after) in plans.items():
            if path.read_bytes() != before:
                raise ValueError(f"конкурентний запис: {path}")
        for path, (_before, after) in plans.items():
            fd, temporary = tempfile.mkstemp(prefix=".uk-projection-", dir=path.parent)
            try:
                with os.fdopen(fd, "wb") as out:
                    os.fchmod(out.fileno(), stat.S_IMODE(path.stat().st_mode))
                    out.write(after)
                    out.flush()
                    os.fsync(out.fileno())
                if path.read_bytes() != _before:
                    raise ValueError(f"конкурентний запис: {path}")
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
    print(
        f"{'APPLY' if apply else 'DRY_RUN'} findings={len(changes)} "
        f"unresolved={len(unresolved)} rewritten_files={len(plans) if apply else 0}"
    )
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--mapping", type=Path, help="явні координатні authority-рішення JSON")
    parser.add_argument("--apply", action="store_true", help="змінювати лише після повного preflight")
    args = parser.parse_args()
    try:
        execute(args.root, args.mapping, args.apply)
    except (ValueError, OSError, UnicodeError, KeyError, json.JSONDecodeError) as error:
        parser.exit(2, f"UK_PROJECTION_REFUSED: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
