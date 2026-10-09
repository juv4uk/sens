#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_binary_language.py — БЕНЧМАРК ядра двійкової мови SENS (модель, не Rust)."""
from __future__ import annotations
import random, sys, time
from typing import List
sys.path.insert(0, ".")
from sens_binary_language_model import Word, pack, unpack

def make_words(n, widths, seed=1234):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        w = rng.choice(widths)
        out.append(Word(w, rng.randrange(1 << w)))
    return out

def bench(words):
    widths = [w.width for w in words]; n = len(words)
    t0 = time.perf_counter(); payload, nbits = pack(words); t_pack = time.perf_counter()-t0
    t0 = time.perf_counter(); back = unpack(payload, widths, nbits); t_unpack = time.perf_counter()-t0
    total_bits = sum(widths); phys = len(payload)*8
    crossed = pos = 0
    for w in words:
        if pos//8 != (pos+w.width-1)//8: crossed += 1
        pos += w.width
    return dict(n=n, bits=total_bits, bytes=len(payload),
                bpw=total_bits/n, bypw=len(payload)/n,
                ovh=(phys-total_bits)/phys*100 if phys else 0.0,
                crossed=crossed/n*100,
                pack_wps=n/t_pack if t_pack else float('inf'),
                unpack_wps=n/t_unpack if t_unpack else float('inf'),
                exact=back==words)

def show(label, r):
    print(f"\n=== {label} ===")
    print(f"  слів:                  {r['n']:,}")
    print(f"  бітів / байтів:        {r['bits']:,} / {r['bytes']:,}")
    print(f"  бітів на слово:        {r['bpw']:.3f}")
    print(f"  байтів на слово:       {r['bypw']:.3f}")
    print(f"  overhead вирівнювання: {r['ovh']:.2f}%")
    print(f"  перетинають байт:      {r['crossed']:.1f}%   <- міра 'справді двійковості'")
    print(f"  пакування:             {r['pack_wps']:,.0f} слів/сек")
    print(f"  розпакування:          {r['unpack_wps']:,.0f} слів/сек")
    print(f"  round-trip точний:     {r['exact']}")

def main():
    full = "--full" in sys.argv
    print("БЕНЧМАРК ЯДРА ДВІЙКОВОЇ МОВИ SENS  (модель, не Rust)")
    print("питання: не 'зелено?', а 'хто ми насправді?'")
    fails = 0
    for label, widths in [("усі ширини 8 (байтово-вирівняні)", [8]),
                          ("ширини 1..=9 рівномірно", list(range(1,10))),
                          ("вузькі 3..=5", [3,4,5]),
                          ("широкі 7..=9", [7,8,9])]:
        r = bench(make_words(100_000, widths)); show(label, r)
        if not r['exact']: print("  !!! round-trip НЕ точний"); fails += 1
    print("\n\n=== МАСШТАБ (ширини 1..=9) ===")
    for n in [1_000, 100_000] + ([1_000_000] if full else []):
        r = bench(make_words(n, list(range(1,10))))
        print(f"  n={n:>9,}  точний={r['exact']}  пак={r['pack_wps']:>12,.0f}/с  розпак={r['unpack_wps']:>12,.0f}/с  байт/слово={r['bypw']:.3f}  перетин={r['crossed']:.0f}%")
        if not r['exact']: fails += 1
    print("\n\n=== ХТО МИ НАСПРАВДІ (висновок) ===")
    b8 = bench(make_words(100_000, [8])); mx = bench(make_words(100_000, list(range(1,10))))
    print(f"  8-бітні: перетин байта = {b8['crossed']:.0f}%  -> це НЕ двійковість, це байтова мова")
    print(f"  1..=9:   перетин байта = {mx['crossed']:.0f}%  -> ось тут механізм справді бітовий")
    print(f"  overhead: 8-біт={b8['ovh']:.2f}%  mixed={mx['ovh']:.2f}%")
    print(f"\nБЕНЧМАРК: {'OK' if fails==0 else 'BROKEN'} ({fails} поломок)")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
