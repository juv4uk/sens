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
from sens_t5_t5m_codec import SensT5Error, decode_bytes, encode_words, typed_sha256


def git(root: Path, *args: str) -> bytes:
    p = subprocess.run(["git", "-C", str(root), *args],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=False, timeout=60)
    if p.returncode:
        raise ValueError(f"git {' '.join(args[:3])} failed: {p.stderr.decode(errors='replace')[:250]}")
    return p.stdout


def tree_modes(root: Path, ref: str) -> dict[str, str]:
    """Read the immutable Git tree, retaining file modes and exact UTF-8 paths.

    A Git symlink (120000) holds its target as a blob. Reading its contents
    with git show is NOT evidence of a regular executable or physical file.
    """
    raw = git(root, "ls-tree", "-r", "-z", "--full-tree", ref)
    modes = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, separator, path = record.partition(b"\t")
        parts = meta.split()
        if not separator or len(parts) != 3:
            raise ValueError("invalid Git tree entry (fail closed)")
        mode, kind, _object_id = parts
        name = path.decode("utf-8", errors="strict")
        if name in modes:
            raise ValueError(f"duplicate Git tree path: {name!r}")
        if kind not in (b"blob", b"commit"):
            raise ValueError(f"unexpected Git tree kind at {name!r}")
        modes[name] = mode.decode("ascii")
    return modes


def files(root: Path, ref: str) -> set[str]:
    return set(tree_modes(root, ref))


def blob(root: Path, ref: str, path: str) -> bytes:
    return git(root, "show", f"{ref}:{path}")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot(root: Path, ref: str) -> dict:
    sha_ref = git(root, "rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    modes = tree_modes(root, sha_ref)
    names = set(modes)
    all_sources = {p for p in names if p.endswith(".lisp")}
    regular = {"100644", "100755"}
    sources = {p for p in all_sources if modes[p] in regular}
    nonregular_sources = sorted(all_sources - sources)
    all_physical = {p for p in names if p.endswith(".sens")}
    physical = {p for p in all_physical if modes[p] in regular}
    nonregular_physical = sorted(all_physical - physical)
    # Keep pairs with an invalid source visible as invalid rows; do not
    # silently erase evidence of an attempted Git triple.
    pairs = sorted(p[:-5] for p in names if p.endswith(".sens") and p[:-5]+".lisp" in all_sources)
    triples = sorted(stem for stem in pairs if stem in names)
    rows = []
    for stem in pairs:
        lisp = stem+".lisp"
        sens = stem+".sens"
        r = {"source": lisp, "physical": sens, "view": stem,
             "has_view": stem in names,
             "scope": "fixture" if stem.startswith("tests/fixtures/") else "non_fixture",
             "semantic_oracle": "NOT_ATTESTED_BY_THIS_MECHANICAL_AUDIT"}
        try:
            # Only regular Git blobs can prove a same-stem physical triple.
            # Symlinks and gitlinks remain visible as invalid rows (not silently
            # absent), so the migration census cannot count them as verified.
            for member in (lisp, sens, stem):
                if member in names and modes[member] not in ("100644", "100755"):
                    raise ValueError(
                        f"not a regular Git file: {member} mode={modes[member]}")
            # Only a regular Git .lisp object may supply source SHA.
            # A 120000 blob is its link target, and a 160000 object is a
            # commit; neither is source text to migrate.
            r["source_sha256"] = sha(blob(root, sha_ref, lisp))
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
    paired_regular_sources = {stem + ".lisp" for stem in pairs} & sources
    return {"commit":sha_ref, "lisp_count":len(sources),
            "nonregular_lisp_count":len(nonregular_sources),
            "nonregular_lisp_paths":nonregular_sources,
            "sens_count":len(physical),
            "nonregular_sens_count":len(nonregular_physical),
            "nonregular_sens_paths":nonregular_physical,
            "paired_count":len(pairs), "triple_count":len(triples),
            "unpaired_count":len(sources)-len(paired_regular_sources),
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
