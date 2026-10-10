"""Негативні вектори: обидві реалізації (Python і Rust) мусять відмовити."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import research_codec as rc
import tb33_tail_research as tb

lines = []


def neg(kind, data, note):
    try:
        if kind == "T5":
            from adaptive_encoder import декодувати_т5
            декодувати_т5(bytes.fromhex(data))
        elif kind == "F3":
            assert data[:2] == "f3"
            rc.decode(bytes.fromhex(data[2:]))
        elif kind == "F4":
            assert data[:2] == "f4"
            tb.decode(bytes.fromhex(data[2:]))
        else:
            raise AssertionError("невідомий вид")
    except Exception:
        lines.append(f"NEG\t{kind}\t{data}")
        return
    raise AssertionError(f"очікувалась відмова: {kind} {data} ({note})")


buckets = rc._buckets()
widths = [w for w, _, _ in buckets]
max_width = widths[-1]

neg("T5", "f3", "T5-байт 243 недійсний")
neg("T5", "f2", "усі трити 2 -> неканонічне доповнення")

for w, lo, hi in buckets:
    used = sum(rc.capacity(n) for n in range(lo, hi + 1))
    if used < (1 << (8 * w)):
        neg("F3", "f3" + used.to_bytes(w, "big").hex(), f"невикористаний код типу {w}")

neg("F3", "f3", "порожнє тіло F3")
neg("F3", "f3" + ("00" * (max_width + 1)), "тіло F3 поза бакетами")

neg("F4", "f4", "порожнє тіло F4")
neg("F4", "f4" + "00", "тіло F4 не кратне 6 байтам")
neg("F4", "f4" + tb.TAIL_CAPACITY.to_bytes(6, "big").hex(), "невикористаний хвіст F4")
neg("F4", "f4" + ("ff" * 6), "перший блок із 22")

print("\n".join(lines))
