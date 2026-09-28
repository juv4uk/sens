#!/usr/bin/env python3
"""#1585: виконуваний свідок E1–E3 для побітового контракту f32.

Реалізує протокол із docs/research/2026-09-28-gpu2-bitwise-contract.md (§5),
ратифікований власником 2026-09-28 (A1: FMA заборонена обом сторонам;
B1: NaN — за тегом, не за payload).

Режими:

  --oracle          надрукувати еталонну таблицю (без виконавців);
  --self-test       перевірити оракул (чистий stdlib, без заліза);
  --run LABEL=CMD   прогнати кейси через виконавця; повторюваний.

Протокол виконавця (механізм, не семантика):

  свідок ставить env WITNESS_CASE, WITNESS_PROGRAM, WITNESS_EXPECTED_BITS
  і запускає CMD через shell; виконавець друкує в stdout рядок
  «BITS=xxxxxxxx» (8 шістнадцяткових цифр — біти f32 результату).
  Відмова виконавця (нема CUDA тощо) — ненульовий exit або відсутність
  BITS: це ІМЕНОВАНА невідповідність, не мовчазний зелений.

Оракул — чистий stdlib, без numpy. Коректність «обчислити у binary64,
округлити до binary32» для + і * двох binary32-вхідних гарантується
класичною умовою подвійного округлення p2 ≥ 2·p1 + 2 (53 ≥ 50)."""

import argparse
import datetime as dt
import os
import pathlib
import re
import struct
import subprocess
import sys
import tempfile

# --- §1 ратифікованого документа: константи E1, біти зафіксовано -----------
A_BITS = 0x3E9C03E1  #  0.3047171
B_BITS = 0xBF851E33  # -1.0399841
C_BITS = 0x3EA26003  #  0.31713876
E1_MULADD_BITS = 0x39796000  # окремі mul+add — еталон A1 (два округлення)
E1_FMA_BITS = 0x3979611E     # FFMA — еталон ПОРУШЕННЯ A1 (одне округлення)

BITS_RE = re.compile(r"(?i)\bbits?[\s=:]+([0-9a-f]{8})\b")


def f32_from_bits(bits):
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def bits_from_f32(x):
    """struct.pack дає одне округлення f64→f32, round-to-nearest-even."""
    return struct.unpack("<I", struct.pack("<f", x))[0]


def mul32(a_bits, b_bits):
    return bits_from_f32(f32_from_bits(a_bits) * f32_from_bits(b_bits))


def add32(a_bits, b_bits):
    return bits_from_f32(f32_from_bits(a_bits) + f32_from_bits(b_bits))


def fma32(a_bits, b_bits, c_bits):
    """Еталон ПОРУШЕННЯ A1: добуток точно, потім одна сума, одне округлення.

    Для констант E1 сума добутку й c точна у f64 (майже-скасування величин
    одного порядку, Sterbenz), тож результат — коректне єдине округлення.
    Поза E1 (експоненти далеко одна від одної) ця емуляція може мати
    подвійне округлення — свідок не використовує її за межами E1."""
    product = f32_from_bits(a_bits) * f32_from_bits(b_bits)  # точний у f64
    return bits_from_f32(product + f32_from_bits(c_bits))


def is_nan_bits(bits):
    return (bits & 0x7F800000) == 0x7F800000 and (bits & 0x007FFFFF) != 0


# --- Кейси свідка ------------------------------------------------------------
# kind: "bitwise" — очікувані біти; "nan" — правило B1 (тег, не payload)
CASES = [
    ("e1_muladd", "bitwise", E1_MULADD_BITS,
     "(a*b)+c окремими mul+add — еталон A1"),
    ("e2_qnan_0div0", "nan", None, "0.0/0.0 → тег NaN (payload не порівнюється)"),
    ("e2_qnan_inf_minus_inf", "nan", None, "inf−inf → тег NaN"),
    ("e2_qnan_sqrt_neg", "nan", None, "sqrt(−1) → тег NaN"),
    ("e3_add_pos0_neg0", "bitwise", 0x00000000, "(+0.0)+(−0.0) → +0.0 (RNE)"),
    ("e3_mul_neg1_pos0", "bitwise", 0x80000000, "(−1.0)·(+0.0) → −0.0"),
]

CASES_BY_NAME = {c[0]: c for c in CASES}


def program_body(case):
    """Шаблон програми українською поверхнею; адаптер виконавця може
    переписати під власний діалект (буфери, fasl), поки не змінює кейс."""
    templates = {
        # короткі літерали: вони округлюються до тих самих бітів A/B/C
        "e1_muladd": "(друк (додати (помножити 0.3047171 -1.0399841) 0.31713876))",
        "e2_qnan_0div0": "(друк (поділити 0.0 0.0))",
        "e2_qnan_inf_minus_inf": "(друк (відняти +inf.0 +inf.0))",
        "e2_qnan_sqrt_neg": "(друк (квадратний-корінь -1.0))",
        "e3_add_pos0_neg0": "(друк (додати 0.0 -0.0))",
        "e3_mul_neg1_pos0": "(друк (помножити -1.0 0.0))",
    }
    return templates[case]


def oracle_rows():
    rows = []
    for name, kind, expected, note in CASES:
        rows.append((name, f"{expected:08x}" if kind == "bitwise" else "nan-tag", note))
    rows.append(("e1_fma_violation_reference", f"{E1_FMA_BITS:08x}",
                 "що дасть CUDA без -fmad=false (порушення A1) — НЕ еталон"))
    return rows


def run_executor(label, command, case, program_path, ledger_fh):
    name, kind, expected, note = case
    env = dict(os.environ)
    env["WITNESS_CASE"] = name
    env["WITNESS_PROGRAM"] = str(program_path)
    env["WITNESS_EXPECTED_BITS"] = f"{expected:08x}" if expected is not None else ""
    proc = subprocess.run(command, shell=True, capture_output=True, text=True,
                          env=env, timeout=600)
    stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    match = BITS_RE.search(proc.stdout or "")
    if proc.returncode != 0:
        verdict = "NAMED-UNAVAILABLE"
    elif match is None:
        verdict = "NO-BITS"
    else:
        bits = int(match.group(1), 16)
        if kind == "nan":
            verdict = "PASS-TAG" if is_nan_bits(bits) else "FAIL-NOT-NAN"
        elif bits == expected:
            verdict = "PASS-BITWISE"
        elif name == "e1_muladd" and bits == E1_FMA_BITS:
            verdict = "FAIL-FMA-CONTRACT"  # виконавець злив a*b+c у FFMA
        else:
            verdict = "FAIL"
    got = match.group(1).lower() if match else "-"
    row = (stamp, name, label, got,
           f"{expected:08x}" if expected is not None else "nan-tag", verdict)
    ledger_fh.write("\t".join(row) + "\n")
    ledger_fh.flush()
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--oracle", action="store_true", help="еталонна таблиця")
    ap.add_argument("--self-test", action="store_true", help="перевірка оракула")
    ap.add_argument("--run", action="append", default=[], metavar="LABEL=COMMAND",
                    help="виконавець (LABEL=команда); повторювати для кількох")
    ap.add_argument("--cases", default=None, help="кома-список кейсів")
    ap.add_argument("--emit-programs", default=None, metavar="DIR",
                    help="записати шаблони програм у DIR і вийти")
    ap.add_argument("--ledger", default=None, metavar="PATH",
                    help="TSV evidence ledger (append)")
    args = ap.parse_args()

    if args.self_test:
        naive = add32(mul32(A_BITS, B_BITS), C_BITS)
        assert naive == E1_MULADD_BITS, f"E1 mul+add: {naive:08x} != {E1_MULADD_BITS:08x}"
        assert fma32(A_BITS, B_BITS, C_BITS) == E1_FMA_BITS, "E1 fma-еталон"
        assert bits_from_f32(f32_from_bits(0x3E9C03E1)) == 0x3E9C03E1
        assert is_nan_bits(0x7FC00000) and is_nan_bits(0xFFC00000)
        assert not is_nan_bits(0x7F800000) and not is_nan_bits(0x00000000)
        assert add32(0x00000000, 0x80000000) == 0x00000000   # (+0)+(−0) → +0
        assert mul32(0xBF800000, 0x00000000) == 0x80000000  # (−1)·(+0) → −0
        print("оракул: OK (E1 mul+add=%08x, fma=%08x)" %
              (E1_MULADD_BITS, E1_FMA_BITS))
        return 0

    if args.oracle:
        print("кейс\tеталон\tпримітка")
        for r in oracle_rows():
            print("\t".join(r))
        return 0

    if args.emit_programs:
        out = pathlib.Path(args.emit_programs)
        out.mkdir(parents=True, exist_ok=True)
        for name, _, _, _ in CASES:
            (out / f"{name}.lisp").write_text(program_body(name) + "\n",
                                             encoding="utf-8")
        print(f"шаблони програм: {out}")
        return 0

    if not args.run:
        ap.error("потрібен --run LABEL=COMMAND, --oracle, --self-test "
                 "або --emit-programs")

    workdir = pathlib.Path(tempfile.mkdtemp(prefix="gpu2-witness-"))
    for name, _, _, _ in CASES:
        (workdir / f"{name}.lisp").write_text(program_body(name) + "\n",
                                              encoding="utf-8")

    cases = (CASES if not args.cases
             else [CASES_BY_NAME[n] for n in args.cases.split(",")])

    ledger_path = args.ledger or str(workdir / "ledger.tsv")
    rows = []
    with open(ledger_path, "a", encoding="utf-8") as fh:
        if fh.tell() == 0:
            fh.write("timestamp_utc\tcase\texecutor\tbits\texpected\tverdict\n")
        for spec in args.run:
            label, command = spec.split("=", 1)
            for case in cases:
                prog = workdir / f"{case[0]}.lisp"
                row = run_executor(label, command, case, prog, fh)
                rows.append(row)
                print(" | ".join(row[1:]))

    print(f"\nledger: {ledger_path}")
    bad = [r for r in rows if r[5] not in ("PASS-BITWISE", "PASS-TAG")]
    if bad:
        print(f"ЧЕРВОНЕ: {len(bad)} з {len(rows)} рядків не пройшли")
        return 1
    print(f"ЗЕЛЕНЕ: {len(rows)} рядків")
    return 0


if __name__ == "__main__":
    sys.exit(main())
