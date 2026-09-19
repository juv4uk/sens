#!/usr/bin/env python3
"""Перевіряє єдину sr/2 byte-SID authority мовних поверхонь.

SID серіалізується як string із рівно 8 біт. UK/EN/SA є рівноправними
людськими поверхнями; sym — окрема спільна немовна нотація.

Ключове правило sr/2: SID є metadata, а не Lisp surface spelling.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
EXCEPTION_STATUSES = {"candidate", "missing", "compatibility-only"}
SID_TOKEN = re.compile(r'^"[01]{8}"$')
FIRST_WAVE = {"uk", "en", "sa"}
NON_HUMAN = {"sym"}


def tokens(source: str) -> list[str]:
    source = "\n".join(line.split(";", 1)[0] for line in source.splitlines())
    return re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', source)


def parse(items: list[str]):
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

    root = one()
    if position != len(items):
        raise ValueError("реєстр повинен мати рівно одну верхньорівневу форму")
    return root


def check(root) -> tuple[int, set[str], int]:
    if not isinstance(root, list) or not root or root[0] != "sr/2":
        raise ValueError("реєстр повинен починатися з (sr/2 ...)")

    seen_ids: set[str] = set()
    all_surfaces: set[str] = set()
    symbolic_count = 0

    for ordinal, entry in enumerate(root[1:]):
        if not isinstance(entry, list) or len(entry) < 2:
            raise ValueError(f"некоректний semantic-запис: {entry!r}")

        identity = entry[0]
        if not isinstance(identity, str) or not SID_TOKEN.fullmatch(identity):
            raise ValueError(
                f"semantic identity повинна бути 8-бітним string: {identity!r}"
            )

        bits = identity[1:-1]
        sid = int(bits, 2)
        if sid != ordinal:
            raise ValueError(
                "SID axis мусить бути щільною й впорядкованою: "
                f"очікував {ordinal:08b}, отримав {bits}"
            )
        if identity in seen_ids:
            raise ValueError(f"дубль semantic identity: {identity}")
        seen_ids.add(identity)

        if sid == 0:
            if entry != [identity, []]:
                raise ValueError(
                    'SID 00000000 мусить бути рівно ground row ("00000000" ())'
                )
            continue

        entry_surfaces: set[str] = set()
        for surface in entry[1:]:
            if not isinstance(surface, list) or len(surface) != 2:
                raise ValueError(
                    f"{bits}: surface має форму (мова назва-або-())"
                )
            language, name = surface
            if not isinstance(language, str):
                raise ValueError(f"{bits}: назва мови має бути атомом")
            if name != [] and not isinstance(name, str):
                raise ValueError(f"{bits}: назва surface має бути атомом або ()")

            if language in entry_surfaces:
                raise ValueError(f"{bits}: дубль surface {language}")
            entry_surfaces.add(language)
            all_surfaces.add(language)

            if isinstance(name, str):
                if name == identity or name == bits:
                    raise ValueError(
                        f"{bits}/{language}: surface name не може підміняти byte SID"
                    )

                clean_name = name[1:-1] if name.startswith('"') and name.endswith('"') else name
                if (
                    language not in NON_HUMAN
                    and clean_name != "—"
                    and not any(character.isalpha() for character in clean_name)
                ):
                    raise ValueError(
                        f"{bits}/{language}: символічне написання {name!r} мусить жити під sym"
                    )

        missing_first_wave = FIRST_WAVE - entry_surfaces
        if missing_first_wave:
            raise ValueError(
                f"{bits}: UK/EN/SA мають бути явними; відсутні: "
                + ", ".join(sorted(missing_first_wave))
            )
        symbolic_count += int("sym" in entry_surfaces)

    if len(seen_ids) != 168:
        raise ValueError(
            f"sr/2 migration expects exactly 168 identities (Canon 0 + 167), got {len(seen_ids)}"
        )
    if len(seen_ids) > 256:
        raise ValueError("semantic registry no longer fits the declared 8-bit SID axis")

    return len(seen_ids), all_surfaces, symbolic_count


def main() -> int:
    try:
        root = parse(tokens(REGISTRY.read_text(encoding="utf-8")))
        count, surfaces, symbolic_count = check(root)
    except (OSError, ValueError) as error:
        print(f"semantic registry error: {error}")
        return 1

    print(f"semantic registry: {count} identities")
    print("surfaces: " + " ".join(sorted(surfaces)))
    print(f"shared symbolic identities: {symbolic_count}")
    print("8-bit SID authority: CONFIRMED")
    print("Canon 0 + contiguous byte axis: CONFIRMED")
    print("SID bitstrings are metadata, not Lisp surfaces: CONFIRMED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
