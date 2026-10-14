#!/usr/bin/env python3
"""Корпус для приймання #5767: реальні .sens (ACCEPT) + негативні фікстури (REJECT).

Пише два списки шляхів, які читає parity_t5.zig (libc, відносно cwd):
  parity_accept.txt — усе фізичне, що мусить пройти decode->encode == байти
  parity_reject.txt — усе, що мусить бути відхилено fail-closed

Не виконує програму, не судить семантику. Лише фізичний транспорт.
"""
from __future__ import annotations
import argparse, os, pathlib, subprocess, sys

# Негативні фікстури за переліком #5767 (фізичні байти T5).
# T5: 5 трітів/байт, тріт 2 = межа слова/доповнення; байти 243..255 недійсні.
NEGATIVES = {
    "neg-invalid-243.sens": bytes([0xF3]),            # недійсний байт 243
    "neg-invalid-255.sens": bytes([0xFF]),            # недійсний байт 255
    "neg-empty.sens": b"",                            # порожній фізичний
    "neg-all-padding.sens": bytes([0xF2]),            # тріти 22222 -> самі розділювачі
    "neg-overwidth.sens": bytes([0x3E, 0x97, 0x07]),  # 12 біт в одному слові (>W11)
}

def tracked_corpus(root: pathlib.Path) -> list[str]:
    """Лише git-tracked .sens: незакомічені файли рою НЕ входять у доказ."""
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "*.sens"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if proc.returncode:
        raise RuntimeError(
            "git ls-files недоступний: "
            + proc.stderr.decode("utf-8", errors="replace").strip()
        )
    # Git -z зберігає шляхи точно; downstream Zig читає manifest по рядках.
    names = [os.fsdecode(item) for item in proc.stdout.split(b"\0") if item]
    if not names:
        raise RuntimeError("немає жодного git-tracked .sens (порожній корпус)")
    if len(set(names)) != len(names):
        raise RuntimeError("дублікати / unmerged записи Git-індексу .sens")
    paths = []
    for name in sorted(names):
        if "\n" in name or "\r" in name:
            raise RuntimeError(f"непредставний CR/LF у назві tracked .sens: {name!r}")
        path = root / name
        if path.is_symlink():
            raise RuntimeError(f"символічне посилання tracked .sens: {name!r}")
        if not path.is_file():
            raise RuntimeError(f"git-tracked .sens відсутній на диску: {name!r}")
        # Складені шляхи через symlink-каталоги також не можуть вийти з root.
        try:
            path.resolve(strict=True).relative_to(root)
        except ValueError as exc:
            raise RuntimeError(f"tracked .sens виходить за межі root: {name!r}") from exc
        paths.append(str(path))
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="корінь репо")
    ap.add_argument("--neg-dir", default="/tmp/t5-negatives", help="куди писати негативи")
    ap.add_argument("--accept", default="parity_accept.txt")
    ap.add_argument("--reject", default="parity_reject.txt")
    a = ap.parse_args()
    root = pathlib.Path(a.root).resolve()

    # Абсолютні шляхи для ручного parity harness; тільки файли індексу Git.
    try:
        accept = tracked_corpus(root)
    except (RuntimeError, OSError) as exc:
        print(f"CORPUS-FAIL-CLOSED: {exc}", file=sys.stderr)
        return 2
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
