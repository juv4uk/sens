#!/usr/bin/env python3
"""Перевіряє canonical 8-bit binary-SID authority мовних поверхонь."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
SID_TOKEN = re.compile(r"^[01]{8}$")
FIRST_WAVE = {"ук", "en", "sa"}
ALL_SURFACES = {"en", "ук", "укр", "sa", "sym"}
NON_HUMAN = {"sym"}


def tokens(source: str) -> list[str]:
    source = "\n".join(line.split(";", 1)[0] for line in source.splitlines())
    return re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', source)


def parse_all(items: list[str]):
    position = 0

    def one():
        nonlocal position
        if position >= len(items):
            raise ValueError("реєстр обірвався посеред форми")
        token = items[position]
        position += 1
        if token != "(":
            if token == ")":
                raise ValueError("неочікувана закривальна дужка")
            return token
        result = []
        while position < len(items) and items[position] != ")":
            result.append(one())
        if position >= len(items):
            raise ValueError("незакритий список")
        position += 1
        return result

    roots = []
    while position < len(items):
        roots.append(one())
    return roots


def check(root) -> tuple[int, set[str], int]:
    if not isinstance(root, list) or not root:
        raise ValueError("реєстр повинен бути непорожнім списком")

    if root[0] == ["binary", "8"]:
        raise ValueError("застарілий заголовок (binary 8) не є рядком Canon")

    entries = root

    seen_ids: set[str] = set()
    all_surfaces: set[str] = set()
    symbolic_count = 0

    for ordinal, entry in enumerate(entries):
        if not isinstance(entry, list) or len(entry) < 2:
            raise ValueError(f"некоректний semantic-запис: {entry!r}")

        identity = entry[0]
        if not isinstance(identity, str) or not SID_TOKEN.fullmatch(identity):
            raise ValueError(
                f"semantic identity повинна бути голим 8-бітним binary token: {identity!r}"
            )

        sid = int(identity, 2)
        if sid != ordinal:
            raise ValueError(
                "SID axis мусить бути щільною й впорядкованою: "
                f"очікував {ordinal:08b}, отримав {identity}"
            )
        if identity in seen_ids:
            raise ValueError(f"дубль semantic identity: {identity}")
        seen_ids.add(identity)

        entry_surfaces: set[str] = set()
        for surface in entry[1:]:
            if not isinstance(surface, list) or len(surface) != 2:
                raise ValueError(
                    f"{identity}: surface має форму (мова назва-або-())"
                )
            language, name = surface
            if not isinstance(language, str):
                raise ValueError(f"{identity}: назва мови має бути атомом")
            if name != [] and not isinstance(name, str):
                raise ValueError(
                    f"{identity}: назва surface має бути атомом або ()"
                )
            if language in entry_surfaces:
                raise ValueError(f"{identity}: дубль surface {language}")
            entry_surfaces.add(language)
            all_surfaces.add(language)

            if isinstance(name, str):
                clean_name = (
                    name[1:-1]
                    if name.startswith('"') and name.endswith('"')
                    else name
                )
                if clean_name == identity:
                    raise ValueError(
                        f"{identity}/{language}: surface name не може підміняти binary SID"
                    )
                if (
                    language not in NON_HUMAN
                    and clean_name != "—"
                    and not any(character.isalpha() for character in clean_name)
                ):
                    raise ValueError(
                        f"{identity}/{language}: символічне написання {name!r} мусить жити під sym"
                    )

        if entry_surfaces != ALL_SURFACES:
            raise ValueError(
                f"{identity}: expected fixed en/ук/укр/sa/sym slots, got "
                f"{sorted(entry_surfaces)}"
            )

        missing_first_wave = FIRST_WAVE - entry_surfaces
        if missing_first_wave:
            raise ValueError(
                f"{identity}: УК/EN/SA мають бути явними; відсутні: "
                + ", ".join(sorted(missing_first_wave))
            )

        symbolic_count += int("sym" in entry_surfaces)

    if len(seen_ids) != 170:
        raise ValueError(
            f"expected exactly 170 identities (Canon 0 + 169), got {len(seen_ids)}"
        )
    if len(seen_ids) > 256:
        raise ValueError("semantic registry no longer fits the declared 8-bit SID axis")

    return len(seen_ids), all_surfaces, symbolic_count


def main() -> int:
    try:
        roots = parse_all(tokens(REGISTRY.read_text(encoding="utf-8")))
        if len(roots) != 1:
            raise ValueError("registry must contain exactly one top-level table form")
        count, surfaces, symbolic_count = check(roots[0])
    except (OSError, ValueError) as error:
        print(f"semantic registry error: {error}")
        return 1

    print(f"semantic registry: {count} identities")
    print("surfaces: " + " ".join(sorted(surfaces)))
    print(f"shared symbolic identities: {symbolic_count}")
    print("8-bit binary SID authority: CONFIRMED")
    print("Canon 0 + contiguous byte axis: CONFIRMED")
    print("Bare binary tokens are canonical: CONFIRMED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
