#!/usr/bin/env python3
"""Порахувати середнє, ДІ95 і висновок про перекриття для dot_bench.

Чому окремий скрипт, а не heredoc у workflow: вкладений heredoc ламається,
і правка не застосовується тихо. Тут файл — цілий, його видно в репозиторії.

Вхід: каталог із n<розмір>.txt, де кожен запуск — ОКРЕМИЙ процес.
Вихід: SUMMARY.txt у тому ж каталозі, ASCII.

Нічого не вигадує: якщо повторів менше двох, пише TOO_FEW_REPS.
"""
import math
import pathlib
import re
import statistics
import sys

# t(0.975, df=7) для 8 незалежних повторів.
T_975_DF7 = 2.365


def ci95(values):
    mean = statistics.mean(values)
    stdev = statistics.stdev(values)
    half = T_975_DF7 * stdev / math.sqrt(len(values))
    return mean, mean - half, mean + half


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "build/dot")
    out = []
    for path in sorted(root.glob("n*.txt")):
        text = path.read_text(encoding="utf-8", errors="replace")
        scalar = [int(x) for x in re.findall(r"SCALAR_WALL_NS (\d+)", text)]
        avx2 = [int(x) for x in re.findall(r"AVX2_WALL_NS (\d+)", text)]
        out.append(f"FILE {path.name} reps={len(scalar)}/{len(avx2)}")
        if len(scalar) < 2 or len(avx2) < 2:
            out.append("  TOO_FEW_REPS")
            continue
        ms, ls, hs = ci95(scalar)
        ma, la, ha = ci95(avx2)
        out.append(f"  SCALAR_MEAN_NS {ms:.0f} CI95 [{ls:.0f}, {hs:.0f}]")
        out.append(f"  AVX2_MEAN_NS {ma:.0f} CI95 [{la:.0f}, {ha:.0f}]")
        out.append(f"  RATIO {ms / ma:.4f}")
        overlap = not (hs < la or ha < ls)
        out.append(f"  CI_OVERLAP {'YES_UNSTABLE' if overlap else 'NO_STABLE'}")
    summary = root / "SUMMARY.txt"
    summary.write_text("\n".join(out) + "\n", encoding="ascii")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
