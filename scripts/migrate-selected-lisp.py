#!/usr/bin/env python3
"""Fail-closed, one-existing-file SENS migration admission.

This is an adapter over migrate-three-pass.py and sens_t5_codec.py,
NOT a new parser, codec, domain table, or semantic oracle.

Proof before publication: immutable Git source blob, explicit historical era
when 8-bit identity is ambiguous, canonical physical T5 bytes, *real* Rust D2
reader, and independent executable oracle attestation. Anything unproved BLOCKS.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from sens_t5_codec import decode_bytes, encode_projection, typed_sha256

SCHEMA = "sens-selected-original-t5/v1"
ORACLE_SCHEMA = "sens-historical-current-oracle/v1"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
BITS8 = re.compile(r"[01]{8}\Z")

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def load_migrator():
    spec = importlib.util.spec_from_file_location("selected_three_pass", SCRIPTS / "migrate-three-pass.py")
    if not spec or not spec.loader:
        raise ValueError("missing canonical three-pass migrator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def selection(path: str) -> tuple[Path, Path]:
    rel = Path(path)
    if rel.is_absolute() or ".." in rel.parts or rel.suffix != ".lisp":
        raise ValueError("source must be a relative tracked .lisp path inside repository")
    source = ROOT / rel
    if source.is_symlink() or not source.is_file() or source.resolve() != ROOT / rel:
        raise ValueError("missing, symlink, or redirected source")
    return rel, source

def pinned_head_blob(rel: Path, requested: str) -> tuple[str, str]:
    """Only a committed Git source, not an untracked or modified workspace file.

    HEAD is a convenience spelling for the exact checked-out commit's blob SHA.
    An explicit SHA must match BOTH HEAD and the source bytes below.
    """
    head = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT,
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    record = subprocess.run(
        ["git", "ls-tree", "-z", "HEAD", "--", rel.as_posix()], cwd=ROOT,
        capture_output=True, check=True,
    ).stdout
    entries = [part for part in record.split(b"\x00") if part]
    if len(entries) != 1:
        raise ValueError("source must exist exactly once as a tracked file at HEAD")
    header, separator, tracked_path = entries[0].partition(b"\t")
    if not separator or tracked_path != rel.as_posix().encode("utf-8"):
        raise ValueError("Git tree source path does not match requested path")
    m = re.fullmatch(rb"100644 blob ([0-9a-f]{40})", header)
    if m is None:
        raise ValueError("source is not a regular tracked Git blob")
    committed_blob = m.group(1).decode("ascii")
    if requested != "HEAD" and requested != committed_blob:
        raise ValueError("source changed: supplied SHA differs from committed HEAD blob")
    return committed_blob, head


def ambiguous_eight_bit_atoms(migration, source: str) -> list[str]:
    # Conservatively examine ALL eight-bit atoms, even quoted data. The
    # migration tool cannot safely guess whether a W8 is legacy or current D8.
    stripped = migration.strip_comments(source)
    return sorted({token.text for token in migration.tokenize(stripped)
                   if token.kind == "ATOM" and BITS8.fullmatch(token.text)})

def check_reader(reader: Path, physical: Path, words: list[str]) -> None:
    if not reader.is_file():
        raise ValueError("reader must be an existing sens-trit executable")
    proc = subprocess.run([str(reader.resolve()), "open", str(physical)],
                          capture_output=True, text=True, timeout=30, check=False)
    if proc.returncode != 0:
        raise ValueError("current SENS Rust D2 reader rejected candidate: " +
                         proc.stderr.strip()[:250])
    if proc.stdout != " ".join(words) + "\n":
        raise ValueError("Rust D2 reader disagrees about exact word boundaries")

def check_oracle(verifier: Path, source: Path, physical: Path,
                 source_blob: str, physical_sha: str, word_sha: str) -> dict:
    if not verifier.is_file() or verifier.is_symlink():
        raise ValueError("oracle must be an independent executable file")
    verifier = verifier.resolve()
    proc = subprocess.run([str(verifier), str(source), str(physical)],
                          capture_output=True, text=True, timeout=60, check=False)
    if proc.returncode != 0:
        raise ValueError("historical/current oracle rejected candidate: " +
                         proc.stderr.strip()[:250])
    try:
        evidence = json.loads(proc.stdout)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("oracle must return one valid JSON evidence object") from exc
    if not isinstance(evidence, dict):
        raise ValueError("oracle evidence must be a JSON object")
    for key, expected in (
        ("schema", ORACLE_SCHEMA),
        ("status", "PASS"),
        ("source_blob_sha", source_blob),
        ("physical_sha256", physical_sha),
        ("typed_word_sha256", word_sha),
    ):
        if evidence.get(key) != expected:
            raise ValueError(f"oracle {key} does not match pinned candidate")
    if ("historical_observable" not in evidence or
            "current_observable" not in evidence or
            evidence["historical_observable"] != evidence["current_observable"]):
        raise ValueError("independent historical/current observations differ or are missing")
    if not isinstance(evidence.get("evidence"), str) or not evidence["evidence"].strip():
        raise ValueError("oracle missing independently reviewable evidence description")
    return {
        "verifier_sha256": sha(verifier.read_bytes()),
        "historical_observable": evidence["historical_observable"],
        "current_observable": evidence["current_observable"],
        "evidence": evidence["evidence"],
    }

def run(args) -> dict:
    rel, source = selection(args.source)
    if args.source_blob != "HEAD" and not HEX40.fullmatch(args.source_blob):
        raise ValueError("source-blob must be HEAD or a pinned 40-hex Git SHA")
    committed_blob, head_commit = pinned_head_blob(rel, args.source_blob)
    raw = source.read_bytes()
    actual_blob = git_blob(raw)
    if committed_blob != actual_blob:
        raise ValueError(f"source changed: expected blob {committed_blob}; actual {actual_blob}")
    source_text = raw.decode("utf-8")
    out_root = args.out_root.resolve()
    out_path = out_root / rel.with_suffix(".sens")
    if out_path.exists() or out_path.is_symlink():
        raise ValueError("same-stem .sens already exists; no overwrite even if identical")
    migration = load_migrator()
    ambiguous = ambiguous_eight_bit_atoms(migration, source_text)
    if ambiguous and args.source_era == "auto":
        raise ValueError("ambiguous W8/D8 words: explicit --source-era and oracle required: " +
                         ", ".join(ambiguous[:8]))
    foundation = migration.load_foundation(ROOT / "knowledge/d1-d9-foundation.json")
    legacy, my, upper = migration.build_three_pass_maps(
        foundation,
        ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry.rs",
        ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
        ROOT / "contracts/core1-historical-sid-map.lisp",
        ROOT / "knowledge/sens8-current-coverage-v1.json",
    )
    text7 = migration.build_text7(
        foundation, ROOT / "crates/sens/src/text7_projection_generated.rs")
    resolver = migration.Resolver(
        legacy, my, upper, source_era=args.source_era,
        admitted_d8=foundation["domains"]["D8"]["residents"],
    )
    try:
        projection = migration.migrate_file(source_text, resolver, text7)
    except migration.MigrationError as exc:
        raise ValueError("three-pass migration BLOCKED: " + str(exc)) from exc
    physical = encode_projection(projection)  # Unknown names/numbers fail here.
    words = decode_bytes(physical)
    if " ".join(words) + "\n" != projection:
        raise ValueError("canonical physical T5 round-trip changed word identity")
    physical_sha, word_sha = sha(physical), typed_sha256(words)
    report = {
        "schema": SCHEMA, "status": "BLOCKED", "source": str(rel),
        "destination": str(rel.with_suffix(".sens")), "source_blob_sha": actual_blob,
        "source_era": args.source_era, "source_commit": head_commit, "binary_bytes": len(physical),
        "physical_sha256": physical_sha, "typed_word_sha256": word_sha,
        "word_count": len(words), "three_pass": dict(resolver.counts),
        "syntax": "NOT_VERIFIED", "oracle": "NOT_VERIFIED",
        "original_491_reduced": False,
    }
    with tempfile.TemporaryDirectory(prefix="sens-t5-selected-") as temp:
        candidate = Path(temp) / "candidate.sens"
        candidate.write_bytes(physical)
        if not args.reader:
            raise ValueError("Rust D2 reader is mandatory; pass --reader")
        check_reader(args.reader, candidate, words)
        report["syntax"] = "PASS_D2_SYNTAX_ONLY"
        if args.inspect:
            # Reader/codec syntax evidence is useful for triage, NOT authority
            # to publish or to claim historical/current semantic parity.
            report["status"] = "SYNTAX_ONLY_UNVERIFIED"
            report["files_written"] = 0
            return report
        if not args.oracle:
            raise ValueError("historical/current independent oracle is mandatory; pass --oracle")
        report["oracle_proof"] = check_oracle(
            args.oracle, source, candidate, actual_blob, physical_sha, word_sha)
        report["oracle"] = "PASS_HISTORICAL_CURRENT"
        if git_blob(source.read_bytes()) != actual_blob:
            raise ValueError("source changed during migration; BLOCK")
        if args.dry_run:
            report["status"] = "VERIFIED_DRY_RUN"
            return report
        # Preserve hierarchy, ensure output root cannot be escaped through symlinks.
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if not out_path.parent.resolve().is_relative_to(out_root):
            raise ValueError("output directory escapes selected output root")
        migration.write_atomic_no_clobber(out_path, physical)
        if git_blob(source.read_bytes()) != actual_blob:
            raise ValueError("source changed after admission; manual investigation required")
    report["status"] = "WRITTEN"
    report["physical_path"] = str(out_path)
    return report

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, help="original tracked repo-relative .lisp")
    ap.add_argument("--source-blob", default="HEAD", help="pinned 40-hex Git blob SHA or checked-out HEAD")
    ap.add_argument("--source-era", choices=("auto", "legacy", "current"), default="auto")
    ap.add_argument("--out-root", required=True, type=Path, help="output hierarchy root")
    ap.add_argument("--reader", type=Path, help="real compiled sens-trit executable")
    ap.add_argument("--oracle", type=Path, help="independent executable verifier, source + staged T5 args")
    ap.add_argument("--report", required=True, type=Path)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="require oracle but do not publish")
    mode.add_argument("--inspect", action="store_true", help="only check physical T5 and real Rust D2; NEVER publish")
    args = ap.parse_args(argv)
    try:
        report = run(args)
        code = 0
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError, ImportError) as exc:
        report = {
            "schema": SCHEMA, "status": "BLOCKED", "source": args.source,
            "source_era": args.source_era, "reason": str(exc)[:600],
            "files_written": 0, "original_491_reduced": False,
        }
        code = 2
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
