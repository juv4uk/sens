#!/usr/bin/env python3
"""Per-message-kind average payload sizes for agent-messages corpus.

Does not need agent_bench / valgrind. Reuses generators from run.py.
Wire/fasl binary sizes remain owned by the full Cachegrind harness
(results/20260930: wire 34.3 B, fasl 154.1 B overall).

  python3 benchmarks/agent-messages/size_by_kind.py [--n 1000] [--seed 1] [--out DIR]
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import marshal
import random
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_run():
    spec = importlib.util.spec_from_file_location("agent_messages_run", HERE / "run.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def avg_len(blobs: list[bytes]) -> float:
    return sum(len(b) for b in blobs) / max(len(blobs), 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", type=Path, default=HERE / "results" / "size-by-kind")
    args = ap.parse_args()
    am = load_run()
    t0 = time.perf_counter()
    rng = random.Random(args.seed)
    messages = [am.gen_message(rng, i) for i in range(args.n)]
    by_kind: dict[str, list] = {}
    for m in messages:
        by_kind.setdefault(m[0], []).append(m)
    by_kind["ALL"] = messages

    rows = []
    for kind in sorted(by_kind.keys(), key=lambda k: (k == "ALL", k)):
        msgs = by_kind[kind]
        en = [am.lisp(m, am.EN).encode() for m in msgs]
        sens = [am.lisp(m, am.SENS).encode() for m in msgs]
        py = [am.python(m).encode() for m in msgs]
        js = [json.dumps(am.json_ast(m), separators=(",", ":")).encode() for m in msgs]
        ma = [marshal.dumps(compile(am.python(m), "<m>", "exec")) for m in msgs]
        rows.append(
            {
                "kind": kind,
                "count": len(msgs),
                "avg_bytes_sens_en": f"{avg_len(en):.3f}",
                "avg_bytes_sens_sid_text": f"{avg_len(sens):.3f}",
                "avg_bytes_py_src": f"{avg_len(py):.3f}",
                "avg_bytes_py_json": f"{avg_len(js):.3f}",
                "avg_bytes_py_marshal": f"{avg_len(ma):.3f}",
                "seed": args.seed,
                "n": args.n,
            }
        )

    elapsed_ms = (time.perf_counter() - t0) * 1000
    args.out.mkdir(parents=True, exist_ok=True)
    tsv = args.out / "size_by_kind.tsv"
    with tsv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {tsv} ({len(rows)} rows, {elapsed_ms:.1f} ms)")
    for r in rows:
        print(
            f"{r['kind']:8} n={r['count']:4}  en={r['avg_bytes_sens_en']:7}  "
            f"sid_text={r['avg_bytes_sens_sid_text']:7}  py={r['avg_bytes_py_src']:7}  "
            f"json={r['avg_bytes_py_json']:7}  marshal={r['avg_bytes_py_marshal']:7}"
        )
    print(
        "note: published sens-wire overall avg 34.3 B / fasl 154.1 B "
        "(results/20260930; needs agent_bench+Cachegrind)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
