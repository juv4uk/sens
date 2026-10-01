#!/usr/bin/env python3
"""Bounded corpus scan for H-NIL: callable NIL operator vs () data.

Does not execute SENS. Counts textual patterns under lib/ and knowledge/.
"""

from __future__ import annotations

import csv
import re
import sys
import time
from pathlib import Path

ROOTS = [Path("lib"), Path("knowledge")]
NIL_CALL = re.compile(r"\(nil[\s)]")
QUOTED_NIL = re.compile(r"\(00000001\s+[nN]il\)|\(quote\s+nil\)", re.I)
EMPTY = re.compile(r"\(\)")
SID0 = re.compile(r"\b00000000\b")


def scan() -> dict:
    stats = {
        "files": 0,
        "nil_call_head": 0,
        "quoted_nil_as_data": 0,
        "empty_list_token": 0,
        "sid_zero_mentions": 0,
    }
    quoted_hits: list[str] = []
    for root in ROOTS:
        if not root.is_dir():
            continue
        for path in root.rglob("*.lisp"):
            stats["files"] += 1
            text = path.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(text.splitlines(), 1):
                if NIL_CALL.search(line):
                    stats["nil_call_head"] += 1
                if QUOTED_NIL.search(line):
                    stats["quoted_nil_as_data"] += 1
                    quoted_hits.append(f"{path}:{i}")
                stats["empty_list_token"] += len(EMPTY.findall(line))
                if SID0.search(line):
                    stats["sid_zero_mentions"] += 1
    stats["quoted_hit_locs"] = ";".join(quoted_hits[:20])
    return stats


def main() -> int:
    t0 = time.perf_counter()
    stats = scan()
    elapsed_ms = (time.perf_counter() - t0) * 1000
    out = Path("docs/research/2019-h-nil-corpus-scan.tsv")
    out.parent.mkdir(parents=True, exist_ok=True)
    # verdict: H-NIL strengthened if no callable heads
    if stats["nil_call_head"] == 0:
        verdict = "supports_H_NIL_conjecture"
    else:
        verdict = "callable_NIL_present_investigate"
    row = {
        "metric": "corpus_scan",
        "files": stats["files"],
        "nil_call_head": stats["nil_call_head"],
        "quoted_nil_as_data": stats["quoted_nil_as_data"],
        "empty_list_token": stats["empty_list_token"],
        "sid_zero_mentions": stats["sid_zero_mentions"],
        "scan_ms": f"{elapsed_ms:.2f}",
        "verdict": verdict,
        "quoted_hit_locs": stats["quoted_hit_locs"],
    }
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()), delimiter="\t")
        w.writeheader()
        w.writerow(row)
    print(f"files={stats['files']} nil_call_head={stats['nil_call_head']} "
          f"quoted_nil={stats['quoted_nil_as_data']} empty_token={stats['empty_list_token']} "
          f"scan_ms={elapsed_ms:.2f} verdict={verdict}")
    if stats["nil_call_head"] != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
