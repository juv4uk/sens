#!/usr/bin/env python3
"""Count REAL new .lisp/.sens/spaced-view Git triples between two commits.

Mechanically validated != semantic-oracle certified. No worktree writes.
The baseline is a Git SHA/ref, not a mutable claim in an issue.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sens_t5_codec import SensT5Error, decode_bytes, encode_words, typed_sha256


def git(root: Path, *args: str) -> bytes:
    p = subprocess.run(["git", "-C", str(root), *args],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=False, timeout=60)
    if p.returncode:
        raise ValueError(f"git {' '.join(args[:3])} failed: {p.stderr.decode(errors='replace')[:250]}")
    return p.stdout


def files(root: Path, ref: str) -> set[str]:
    # Never shell interpolate untrusted revs/paths; commit resolve below.
    blob = git(root, "ls-tree", "-r", "-z", "--name-only", ref)
    return {s.decode("utf-8", errors="strict")
            for s in blob.split(b"\0") if s}


def blob(root: Path, ref: str, path: str) -> bytes:
    return git(root, "show", f"{ref}:{path}")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot(root: Path, ref: str) -> dict:
    sha_ref = git(root, "rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    names = files(root, sha_ref)
    sources = {p for p in names if p.endswith(".lisp")}
    pairs = sorted(p[:-5] for p in names if p.endswith(".sens") and p[:-5]+".lisp" in sources)
    triples = sorted(stem for stem in pairs if stem in names)
    rows = []
    for stem in pairs:
        lisp = stem+".lisp"
        sens = stem+".sens"
        r = {"source": lisp, "physical": sens, "view": stem,
             "source_sha256": sha(blob(root, sha_ref, lisp)),
             "has_view": stem in names,
             "scope": "fixture" if stem.startswith("tests/fixtures/") else "non_fixture",
             "semantic_oracle": "NOT_ATTESTED_BY_THIS_MECHANICAL_AUDIT"}
        try:
            packed = blob(root, sha_ref, sens)
            words = decode_bytes(packed)
            if encode_words(words) != packed:
                raise ValueError("not canonical T5 bytes")
            r.update(physical_sha256=sha(packed), physical_bytes=len(packed),
                     typed_sha256=typed_sha256(words), exact_word_count=len(words))
            if stem not in names:
                raise ValueError("missing same-stem extensionless view")
            expected = (" ".join(words)+"\n").encode("ascii")
            if blob(root, sha_ref, stem) != expected:
                raise ValueError("view differs from exact T5 decoded words")
            blob(root, sha_ref, lisp).decode("utf-8", errors="strict")
            r["status"] = "MECHANICAL_TRIPLE_VERIFIED"
        except (ValueError, UnicodeError, SensT5Error) as e:
            r["status"] = "INVALID_OR_INCOMPLETE_TRIPLE"
            r["reason"] = str(e)
        rows.append(r)
    return {"commit":sha_ref, "lisp_count":len(sources),
            "sens_count":sum(p.endswith(".sens") for p in names),
            "paired_count":len(pairs), "triple_count":len(triples),
            "unpaired_count":len(sources)-len(pairs),
            "valid_triples":sum(r["status"]=="MECHANICAL_TRIPLE_VERIFIED" for r in rows),
            "invalid_triples":sum(r["status"]!="MECHANICAL_TRIPLE_VERIFIED" for r in rows),
            "rows":rows}


def difference(root: Path, base: str, head: str) -> dict:
    b, h = snapshot(root, base), snapshot(root, head)
    previous = {x["source"]:x for x in b["rows"]}
    current = {x["source"]:x for x in h["rows"]}
    fresh = sorted(set(current)-set(previous))
    lost = sorted(set(previous)-set(current))
    # Existing test fixtures are not fresh historical executable migration.
    new_rows = [current[x] for x in fresh]
    # Pair != triple: a missing/wrong view is NOT a completed migration.
    verified_new = [x for x in new_rows if x["status"]=="MECHANICAL_TRIPLE_VERIFIED"]
    repaired = sorted(
        key for key in set(current)&set(previous)
        if previous[key]["status"] != "MECHANICAL_TRIPLE_VERIFIED"
        and current[key]["status"] == "MECHANICAL_TRIPLE_VERIFIED"
    )
    return {"schema":"sens-git-physical-triple-delta/v1", "base":b["commit"],
            "head":h["commit"],
            "base_census":{k:v for k,v in b.items() if k not in ("rows","commit")},
            "head_census":{k:v for k,v in h.items() if k not in ("rows","commit")},
            "new_pairs":len(fresh),
            "new_triples":len(verified_new),
            "new_non_fixture_triples":sum(x["scope"]=="non_fixture" for x in verified_new),
            "new_fixture_triples":sum(x["scope"]=="fixture" for x in verified_new),
            "new_mechanically_verified":len(verified_new),
            "repaired_existing_triples":repaired,
            "new_invalid_or_incomplete":sum(x["status"]!="MECHANICAL_TRIPLE_VERIFIED" for x in new_rows),
            "removed_pairs":lost,
            "new_files":new_rows,
            "oracle_certified_original_executables": None,
            "oracle_note":"NOT MEASURED: mechanical triple presence is NOT proof of executable semantics",
            "new_ukrainian_canonical_admissions":None,
            "uk_note":"NOT MEASURED: exact Ukrainian language canonical/semantic parity requires separate verified oracle witnesses"}


def main(argv: list[str] | None = None) -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument("--base",required=True,help="immutable Git SHA or resolving ref")
    ap.add_argument("--head",required=True,help="immutable Git SHA or resolving ref")
    ap.add_argument("--strict",action="store_true",help="fail if any invalid/incomplete pairs or removed pairs")
    args=ap.parse_args(argv)
    try:
        result=difference(args.root.resolve(),args.base,args.head)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        bad=result["head_census"]["invalid_triples"] or result["removed_pairs"]
        return 2 if args.strict and bad else 0
    except (ValueError,subprocess.TimeoutExpired,OSError) as e:
        print(f"MIGRATION GIT DELTA BLOCKED: {e}",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
