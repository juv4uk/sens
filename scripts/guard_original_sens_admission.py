#!/usr/bin/env python3
"""Proof-carrying release gate for additions/changes of ORIGINAL .lisp → .sens.

No parser, domain, codec or semantic law is implemented here. For every
physically new/changed .sens whose .lisp existed in the base Git commit,
require an approved immutable manifest AND actually execute the existing
three-pass -> T5 -> Rust D2 -> named independent-oracle publisher.

New source+new .sens fixtures are reported NEW_COHORT, not an original
migration. Untouched historical artifacts are not silently certified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
SCHEMA = "sens-original-proof-carrying-gate/v1"
MANIFEST_DIR = Path("knowledge/migration-admissions")
SHA = re.compile(r"^[0-9a-f]{40}$")


class Blocked(Exception):
    pass


def call(*argv: str, cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            list(argv), cwd=cwd, capture_output=True, check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Blocked("PROCESS: " + str(exc)) from exc


def git(root: Path, *args: str) -> bytes:
    proc = call("git", *args, cwd=root)
    if proc.returncode:
        raise Blocked("GIT: " + proc.stderr.decode("utf-8", "replace")[-450:])
    return proc.stdout


def changed_sens_paths(root: Path, base: str) -> list[Path]:
    if not SHA.fullmatch(base):
        raise Blocked("BASE: full immutable 40-hex Git commit required")
    git(root, "rev-parse", "--verify", base + "^{commit}")
    changed = git(root, "diff", "--name-only", "-z", "--no-renames",
                  "--diff-filter=AM", base, "HEAD")
    result = []
    for name in changed.split(b"\0"):
        if not name:
            continue
        decoded = name.decode("utf-8", "surrogateescape")
        path = Path(decoded)
        if path.suffix == ".sens":
            if path.is_absolute() or ".." in path.parts:
                raise Blocked("PATH: unsafe Git change")
            result.append(path)
    return sorted(set(result), key=lambda item: item.as_posix())


def old_source_blob(root: Path, base: str, source: Path) -> str | None:
    proc = call("git", "rev-parse", "--verify", f"{base}:{source.as_posix()}",
                cwd=root)
    if proc.returncode != 0:
        return None
    blob = proc.stdout.decode("ascii", "strict").strip()
    if not SHA.fullmatch(blob):
        raise Blocked("GIT: old source blob invalid")
    return blob


def source_and_binary(root: Path, path: Path) -> tuple[Path, Path]:
    if path.suffix != ".sens" or path.is_absolute() or ".." in path.parts:
        raise Blocked("PATH: expected safe .sens relative path")
    source = path.with_suffix(".lisp")
    for target in (source, path):
        current = root
        for piece in target.parts:
            current = current / piece
            if current.is_symlink():
                raise Blocked("PATH: symlink source or binary forbidden")
        if not current.is_file():
            raise Blocked("PATH: missing .lisp/.sens pair: " + str(target))
    return root / source, root / path


def manifests_for(root: Path, source: Path) -> list[tuple[Path, dict]]:
    manifests = []
    for file in sorted((root / MANIFEST_DIR).glob("*.json")):
        if file.is_symlink():
            raise Blocked("MANIFEST: symlink rejected")
        try:
            obj = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise Blocked(f"MANIFEST: invalid {file.name}: {exc}") from exc
        if isinstance(obj, dict) and obj.get("source") == source.as_posix():
            manifests.append((file, obj))
    return manifests


def attest(root: Path, reader: Path, file: Path, manifest: Path,
           mirror: Path) -> dict:
    report = mirror.parent / "publisher-report.json"
    command = [
        sys.executable, str(root / "scripts/admit-t5-migration.py"),
        "--root", str(root), "--manifest", str(manifest),
        "--mirror", str(mirror), "--reader", str(reader),
        "--report", str(report), "--write",
    ]
    run = call(*command, cwd=root, timeout=400)
    state = {}
    if report.is_file():
        try:
            state = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}
    if run.returncode or state.get("status") != "WRITTEN":
        reason = state.get("reason") or run.stderr.decode("utf-8", "replace")[-300:]
        raise Blocked("ORACLE/PHYSICAL/D2: publisher BLOCKED: " + str(reason)[:550])
    target = mirror / file
    if not target.is_file() or target.is_symlink():
        raise Blocked("OUTPUT: publisher created no regular .sens")
    if target.read_bytes() != (root / file).read_bytes():
        raise Blocked("OUTPUT: committed .sens not byte-identical to independently admitted T5")
    return {
        "physical_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "d2_reader": state.get("d2_reader"),
        "oracle_commands_passed": state.get("oracle_commands_passed", 0),
        "publisher_status": state.get("status"),
    }


def inspect(root: Path, base: str, reader: Path,
            attestor=attest) -> dict:
    root = root.resolve(strict=True)
    reader = reader.resolve(strict=True)
    if not reader.is_file() or reader.is_symlink():
        raise Blocked("READER: require actual compiled Rust D2 sens-trit")
    changed = changed_sens_paths(root, base)
    rows = []
    for binary in changed:
        source = binary.with_suffix(".lisp")
        row = {"sens": binary.as_posix(), "source": source.as_posix(),
               "status": "BLOCKED", "semantic_oracle": "NOT_VERIFIED"}
        rows.append(row)
        # All candidate Git outputs must be regular source/target pairs.
        source_file, binary_file = source_and_binary(root, binary)
        prior = old_source_blob(root, base, source)
        if prior is None:
            row["status"] = "NEW_COHORT_NOT_ORIGINAL"
            continue
        row["original_git_blob_sha"] = prior
        # Git HEAD (the actual proposed PR content) and the working bytes
        # BOTH must preserve the base blob; a dirty worktree must not hide a
        # committed source mutation that would silently ship at merge time.
        head_blob = old_source_blob(root, git(root, "rev-parse", "HEAD").decode().strip(), source)
        current_blob = git(root, "hash-object", "--", source.as_posix()).decode().strip()
        if head_blob != prior or current_blob != prior:
            row["reason"] = "SOURCE_CHANGED: committed HEAD and working original must match immutable base"
            continue
        found = manifests_for(root, source)
        if len(found) != 1:
            row["reason"] = f"MANIFEST: exactly one independent source-specific proof required (found {len(found)})"
            continue
        manifest_file, proof = found[0]
        row["manifest"] = manifest_file.relative_to(root).as_posix()
        physical_hash = hashlib.sha256(binary_file.read_bytes()).hexdigest()
        if proof.get("source_git_blob_sha1") != prior:
            row["reason"] = "SOURCE_PROVENANCE: manifest Git blob differs from original"
            continue
        if proof.get("expected_physical_sha256") != physical_hash:
            row["reason"] = "PHYSICAL: manifest SHA256 differs from checked-in file"
            continue
        with tempfile.TemporaryDirectory(prefix="sens-proof-carrying-") as td:
            temp = Path(td)
            try:
                witness = attestor(root, reader, binary, manifest_file, temp / "mirror")
            except Blocked as exc:
                row["reason"] = str(exc)
                continue
        row.update(witness)
        if row.get("d2_reader") != "PASS" or int(row.get("oracle_commands_passed", 0)) < 1:
            row["reason"] = "ORACLE: no independent semantic witness execution"
            continue
        row["status"] = "PROOF_GATE_PASS"
        row["semantic_oracle"] = "NAMED_TESTS_PASSED_REVIEW_REQUIRED"
    failed = sum(row["status"] == "BLOCKED" for row in rows)
    return {
        "schema": SCHEMA,
        "base_git_sha": base,
        "status": "BLOCKED" if failed else "EVIDENCE_CHECKED",
        "summary": {
            "changed_sens_files": len(rows),
            "original_files_proof_checked": sum(r["status"] == "PROOF_GATE_PASS" for r in rows),
            "new_cohorts_not_original_credit": sum(r["status"] == "NEW_COHORT_NOT_ORIGINAL" for r in rows),
            "blocked": failed,
            "automatic_semantic_certification": 0,
        },
        "files": rows,
        "warning": "Named oracles must be independently code-reviewed; transport/D2 alone is not semantic equivalence.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=REPO)
    p.add_argument("--base-sha", required=True)
    p.add_argument("--reader", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path)
    args = p.parse_args()
    try:
        state = inspect(args.root, args.base_sha, args.reader)
        rc = 2 if state["status"] == "BLOCKED" else 0
    except (Blocked, OSError, ValueError, UnicodeError) as exc:
        state = {"schema": SCHEMA, "status": "BLOCKED", "reason": str(exc)}
        rc = 2
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": state["status"], "summary": state.get("summary"),
                      "reason": state.get("reason")}, ensure_ascii=False))
    for entry in state.get("files", []):
        print(entry["status"], entry["sens"], entry.get("reason", ""),flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
