#!/usr/bin/env python3
"""Корпус для приймання #5767: реальні .sens (ACCEPT) + негативні фікстури (REJECT).

Пише два списки шляхів, які читає parity_t5.zig (libc, відносно cwd):
  parity_accept.txt — усе фізичне, що мусить пройти decode->encode == байти
  parity_reject.txt — усе, що мусить бути відхилено fail-closed

Не виконує програму, не судить семантику. Лише фізичний транспорт.
"""
from __future__ import annotations
import argparse, pathlib, sys

# Негативні фікстури за переліком #5767 (фізичні байти T5).
# T5: 5 трітів/байт, тріт 2 = межа слова/доповнення; байти 243..255 недійсні.
NEGATIVES = {
    "neg-invalid-243.sens": bytes([0xF3]),            # недійсний байт 243
    "neg-invalid-255.sens": bytes([0xFF]),            # недійсний байт 255
    "neg-empty.sens": b"",                            # порожній фізичний
    "neg-all-padding.sens": bytes([0xF2]),            # тріти 22222 -> самі розділювачі
    "neg-overwidth.sens": bytes([0x3E, 0x97, 0x07]),  # 12 біт в одному слові (>W11)
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="корінь репо")
    ap.add_argument("--neg-dir", default="/tmp/t5-negatives", help="куди писати негативи")
    ap.add_argument("--accept", default="parity_accept.txt")
    ap.add_argument("--reject", default="parity_reject.txt")
    a = ap.parse_args()
    root = pathlib.Path(a.root).resolve()

    # Абсолютні шляхи: інструмент біжить із власної теки, не з кореня репо.
    accept = sorted(str(p) for p in root.rglob("*.sens")
                    if ".git" not in p.parts and "target" not in p.parts)
    pathlib.Path(a.accept).write_text("\n".join(accept) + "\n", encoding="utf-8")

    negdir = pathlib.Path(a.neg_dir); negdir.mkdir(parents=True, exist_ok=True)
    reject = []
    for name, blob in NEGATIVES.items():
        (negdir / name).write_bytes(blob)
        reject.append(str(negdir / name))
    pathlib.Path(a.reject).write_text("\n".join(reject) + "\n", encoding="utf-8")

    print(f"ACCEPT: {len(accept)} реальних .sens", file=sys.stderr)
    print(f"REJECT: {len(reject)} негативних фікстур", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
