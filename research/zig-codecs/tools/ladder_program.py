#!/usr/bin/env python3
"""Драбина доменів -> точні слова (нова реальність, Zig-кодеки).

Ширина слова Є ідентичністю: Dn = n біт. Жодного історичного реєстру імен,
жодного старого Rust/Python-кодека. Цей модуль лише *будує й перевіряє*
послідовність точних слів; фізичні байти дає сам Zig-кодек (t5.zig/f3c.zig).

Формат входу (по слову в рядку): "<Dn> <bits>" або "<n> <bits>", напр.
    D2 10
    D3 111
    D2 00

Виходи:
  * lines  — простий формат "width bits" (для Zig-інструментів, через stdin/файл)
  * json   — [{width, bits}]
  * view   — канонічний бітовий запис: точні слова через один пробіл
"""
from __future__ import annotations
import argparse, json, pathlib, re, sys

TOKEN = re.compile(r"(?:D)?([1-9]|10)\Z")


class LadderError(ValueError):
    """Неканонічне або недопустиме слово драбини."""


def parse_source(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        parts = line.split()
        if len(parts) != 2:
            raise LadderError(f"рядок {lineno}: очікую '<Dn> <bits>', маю {line!r}")
        tag, bits = parts
        m = TOKEN.fullmatch(tag)
        if not m:
            raise LadderError(f"рядок {lineno}: ширина мусить бути D1..D10, маю {tag!r}")
        width = int(m.group(1))
        if not re.fullmatch(r"[01]+", bits):
            raise LadderError(f"рядок {lineno}: біти мусять бути [01]+, маю {bits!r}")
        if len(bits) != width:
            raise LadderError(
                f"рядок {lineno}: D{width} вимагає рівно {width} біт, маю {len(bits)} ({bits!r})"
            )
        out.append((width, bits))
    if not out:
        raise LadderError("порожня програма")
    return out


def bits_to_int(bits: str) -> int:
    return int(bits, 2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="файл із словами драбини ('<Dn> <bits>' у рядку)")
    ap.add_argument("--lines", help="куди записати формат 'width bits' для Zig")
    ap.add_argument("--json", dest="json_out", help="куди записати [{width,bits}]")
    ap.add_argument("--view", help="куди записати канонічний бітовий запис")
    a = ap.parse_args()

    words = parse_source(pathlib.Path(a.source).read_text(encoding="utf-8"))
    lines = "".join(f"{w} {bits_to_int(b)}\n" for w, b in words)
    view = " ".join(b for _, b in words) + "\n"
    if a.lines:
        pathlib.Path(a.lines).write_text(lines, encoding="utf-8")
    if a.json_out:
        pathlib.Path(a.json_out).write_text(
            json.dumps([{"width": w, "bits": bits_to_int(b)} for w, b in words],
                       ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if a.view:
        pathlib.Path(a.view).write_text(view, encoding="utf-8")
    if not (a.lines or a.json_out or a.view):
        sys.stdout.write(view)
    print(f"слів: {len(words)}; ширини: {sorted({w for w, _ in words})}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
