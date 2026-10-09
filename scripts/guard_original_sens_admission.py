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
import importlib.util
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


def reviewed_source_kind_guard(root: Path, source: Path) -> None:
    """Use SAME immutable nonprogram/archival policy as the production operator.

    This is not semantic admission: outside the reviewed exclusions, program
    classification and original-current oracle still require independent proof.
    """
    path = root / "scripts/migrate-sens.py"
    if not path.is_file() or path.is_symlink():
        raise Blocked("SOURCE_KIND: canonical nonprogram authority unavailable")
    spec = importlib.util.spec_from_file_location("sens_original_kind_operator", path)
    if spec is None or spec.loader is None:
        raise Blocked("SOURCE_KIND: cannot load canonical operator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        module.reject_classified_nonprogram([source.as_posix()], root)
    except (OSError, ValueError, ImportError) as exc:
        raise Blocked("SOURCE_KIND: " + str(exc)) from exc


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


def expected_current_execution(proof: dict) -> bytes:
    """Owner-reviewed exact current-runtime observable, not a D2-only check.

    This must be paired with a genuinely independent source-side oracle;
    an arbitrary claimed output alone is never proof of old/current parity.
    """
    expected = proof.get("expected_current_eval_stdout")
    if not isinstance(expected, str) or not expected or len(expected.encode("utf-8")) > 16384:
        raise Blocked("CURRENT_EVAL: reviewed expected_current_eval_stdout must be nonempty UTF-8 (<=16 KiB)")
    if "\r" in expected or not expected.endswith("\n"):
        raise Blocked("CURRENT_EVAL: stdout must be exact LF-terminated output")
    return expected.encode("utf-8")


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
    # D2 open does not execute the artifact. Require the real capability-free
    # CURRENT SENS runtime to execute these exact SOURCE-derived physical bytes.
    # Nonzero exit, unexpected host output or any stdout drift must BLOCK.
    proof = json.loads(manifest.read_text(encoding="utf-8"))
    expected = expected_current_execution(proof)
    result = call(str(reader), "eval", str(target), cwd=root, timeout=60)
    if result.returncode != 0:
        error = result.stderr.decode("utf-8", "replace")[-350:]
        raise Blocked(f"CURRENT_EVAL: actual sens-trit eval rejected physical .sens: {error}")
    if result.stderr:
        raise Blocked("CURRENT_EVAL: unexpected stderr from current pure SENS runtime")
    if result.stdout != expected:
        raise Blocked("CURRENT_EVAL: exact historical-contract expected stdout differs from real current .sens execution")
    return {
        "physical_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "d2_reader": state.get("d2_reader"),
        "current_eval": "PASS",
        "current_eval_stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "oracle_commands_passed": state.get("oracle_commands_passed", 0),
        "publisher_status": state.get("status"),
    }


def inspect(root: Path, base: str, reader: Path,
            attestor=attest, kind_guard=reviewed_source_kind_guard) -> dict:
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
        # The proposed COMMIT is the release artifact, not the agent's local
        # worktree. Manifest and publisher digest checks on working bytes alone
        # can falsely approve a dirty replacement absent from Git HEAD.
        head_binary_blob = old_source_blob(root, "HEAD", binary)
        working_binary_blob = git(root, "hash-object", "--", binary.as_posix()).decode("ascii").strip()
        if head_binary_blob is None or head_binary_blob != working_binary_blob:
            row["reason"] = "PHYSICAL_HEAD_DRIFT: committed binary must equal working T5 bytes"
            continue
        try:
            kind_guard(root, source)
        except Blocked as exc:
            row["reason"] = str(exc)
            continue
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
        try:
            expected_current_execution(proof)
        except Blocked as exc:
            row["reason"] = str(exc)
            continue
        with tempfile.TemporaryDirectory(prefix="sens-proof-carrying-") as td:
            temp = Path(td)
            try:
                witness = attestor(root, reader, binary, manifest_file, temp / "mirror")
            except Blocked as exc:
                row["reason"] = str(exc)
                continue
        row.update(witness)
        if (row.get("d2_reader") != "PASS" or row.get("current_eval") != "PASS"
                or int(row.get("oracle_commands_passed", 0)) < 1):
            row["reason"] = "ORACLE/CURRENT_EVAL: source-specific oracle and actual .sens execution required"
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
