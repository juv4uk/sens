#!/usr/bin/env python3
"""Сканер ПОХІДНИХ файлів: чи не застаріли вони щодо своїх джерел.

Першопричина: у lib/ знайшлись ДВА застарілі безрозширені вигляди (lib/core,
lib/guard) — випадково, бо їх виявив лише T5-аудит і лише як «BLOCKED». Ніщо не
міряло дерево ЦІЛОМУ. Випадкова знахідка — не міра.

Похідні зв'язки, які перевіряються:
  • X.sens → X (безрозширений канонічний spaced-bit вигляд): мусить дорівнювати
    (" ".join(decode_bytes(X.sens)) + "\n") у ASCII;
  • X.sens → чи декодується взагалі (канонічний T5M, не legacy T5).

Нічого не змінює — лише міряє.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from sens_t5_t5m_codec import decode_bytes, decode_t5m_bytes
except Exception as exc:  # pragma: no cover
    print(f"кодек недоступний: {exc}", file=sys.stderr)
    raise SystemExit(2)

# Архівні/заміщені гілки — окремий кошик: це історія, не поточне виконання.
ARCHIVE_MARKERS = ("superseded", "archive", "/history/", "staged-out")


def decode_any(data: bytes) -> tuple[list[str], str]:
    """ДВА декодери, а не один. decode_bytes — ЛЕГАСІ T5; decode_t5m_bytes — T5M.
    Виклик лише decode_bytes дав ХИБНУ ТРИВОГУ «439 не декодується», хоча всі
    1530 файлів декодуються як T5M. Це виправлено тут."""
    last: Exception | None = None
    for fn, decoder in (("decode_t5m_bytes", decode_t5m_bytes),
                        ("decode_bytes", decode_bytes)):
        try:
            return decoder(data), fn
        except Exception as exc:  # noqa: BLE001
            last = exc
    raise last if last else RuntimeError("жоден декодер")


def tracked_sens() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z", "--", "*.sens"],
                         capture_output=True, text=True, cwd=ROOT).stdout
    return [p for p in out.split("\0") if p]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="fail-closed: жодного застарілого вигляду в активному дереві")
    args = ap.parse_args()
    ok = stale = noview = 0
    undecodable: list[str] = []
    stale_active: list[str] = []
    for rel in tracked_sens():
        path = ROOT / rel
        view = path.with_suffix("")
        try:
            words, _decoder = decode_any(path.read_bytes())
        except Exception:
            undecodable.append(rel)
            continue
        if not view.is_file():
            noview += 1
            continue
        canonical = (" ".join(words) + "\n").encode("ascii")
        if canonical == view.read_bytes():
            ok += 1
        else:
            stale += 1
            if not any(m in rel for m in ARCHIVE_MARKERS):
                stale_active.append(rel)
    archived = sum(1 for u in undecodable if any(m in u for m in ARCHIVE_MARKERS))
    print(f"DERIVED-DRIFT: *.sens={ok + stale + noview + len(undecodable)} "
          f"вигляд-канонічний={ok} вигляд-ЗАСТАРІЛИЙ={stale} вигляду-немає={noview} "
          f"НЕ-ДЕКОДУЄТЬСЯ={len(undecodable)} (з них архівних={archived})")
    for s in stale_active:
        print(f"  ЗАСТАРІЛИЙ (активний): {s}")
    if args.check and stale_active:
        raise SystemExit(f"FAIL: застарілі вигляди в активному дереві: {stale_active}")
    if args.check:
        print("DERIVED-DRIFT: PASS застарілих виглядів в активному дереві немає")
    return 0


if __name__ == "__main__":
    sys.exit(main())
