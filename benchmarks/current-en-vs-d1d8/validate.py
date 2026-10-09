#!/usr/bin/env python3
import argparse, json, re, sys
from collections import defaultdict
from pathlib import Path

SCHEMA="sens-current-en-vs-d1d8/v1"
CANDIDATES={"ukrainian-surface","canonical-d1d8"}
SHA40=re.compile(r"^[0-9a-f]{40}$")
SHA64=re.compile(r"^[0-9a-f]{64}$")

def validate_file(path):
    rows=[]
    for line_no,raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
        if not raw.strip():
            continue
        row=json.loads(raw)
        if row.get("schema") != SCHEMA:
            raise ValueError(f"line {line_no}: wrong schema")
        if row.get("candidate") not in CANDIDATES:
            raise ValueError(f"line {line_no}: current candidates only")
        if row.get("language_model") != "D1-D8":
            raise ValueError(f"line {line_no}: language_model must be D1-D8")
        if row.get("legacy_identity_used") is not False:
            raise ValueError(f"line {line_no}: legacy identity is forbidden")
        if row.get("oracle_ok") is not True:
            raise ValueError(f"line {line_no}: oracle must pass before measurement")
        if not SHA40.fullmatch(row.get("git_sha","")):
            raise ValueError(f"line {line_no}: invalid git_sha")
        for key in ("binary_sha256","corpus_sha256"):
            if not SHA64.fullmatch(row.get(key,"")):
                raise ValueError(f"line {line_no}: invalid {key}")
        rows.append(row)
    if not rows:
        raise ValueError("evidence file is empty")

    groups=defaultdict(list)
    ids=set()
    for row in rows:
        case_id=row["case_id"]
        if case_id in ids:
            raise ValueError(f"duplicate case_id {case_id}")
        ids.add(case_id)
        key=(row["pair_id"],row["lane"],row["workload"],row["phase"],row["rep"])
        groups[key].append(row)

    for key,pair in groups.items():
        if len(pair)!=2 or {r["candidate"] for r in pair} != CANDIDATES:
            raise ValueError(f"incomplete pair {key}")
        for field in ("git_sha","binary_sha256","corpus_sha256"):
            if len({r[field] for r in pair}) != 1:
                raise ValueError(f"pair {key} mismatches {field}")
        if len({json.dumps(r["provenance"],sort_keys=True) for r in pair}) != 1:
            raise ValueError(f"pair {key} mismatches provenance")
    return len(rows),len(groups)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("jsonl",type=Path,nargs="+")
    args=ap.parse_args()
    for path in args.jsonl:
        rows,pairs=validate_file(path)
        print(f"validated {rows} rows / {pairs} pairs: {path}")
    return 0

if __name__=="__main__":
    try:
        sys.exit(main())
    except (OSError,ValueError,json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        sys.exit(2)
