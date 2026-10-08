#!/usr/bin/env python3
"""Proof-gated publisher for ONE real historical Lisp -> physical T5 SENS pair.

This tool does NOT infer SENS meaning: the owner-ratified three-pass migrator
and codec do that. A separate, source-pinned oracle test must succeed before
a binary output can be published. For D8/current-era ambiguities, BLOCK.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
MIGRATOR = REPO / "scripts/migrate-three-pass.py"
sys.path.insert(0, str(REPO / "scripts"))
from sens_t5_codec import decode_bytes, encode_projection, typed_sha256  # noqa: E402

SCHEMA = "sens-t5-proof-admission/v1"
ARTIFACTS = {
    "foundation": "knowledge/d1-d7-foundation.json",
    "domain-surfaces": "crates/sens/src/domain_surface_registry_generated.rs",
    "semantic-generated": "crates/sens/src/semantic_registry_generated.rs",
    "semantic-registry": "crates/sens/src/semantic_registry.rs",
    "necessary-forms": "crates/sens/src/eval/necessary_forms_generated.rs",
    "historical-map": "contracts/core1-historical-sid-map.lisp",
    "text7": "crates/sens/src/text7_projection_generated.rs",
}


class Blocked(Exception):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def inside_root(root: Path, name: str) -> Path:
    candidate = Path(name)
    if candidate.is_absolute() or not candidate.parts or any(
        part in (".", "..") for part in candidate.parts
    ):
        raise Blocked("SOURCE_PATH: source must be repository-relative")
    if candidate.suffix != ".lisp":
        raise Blocked("SOURCE_PATH: source must end with .lisp")
    if not (root / candidate).resolve().is_relative_to(root):
        raise Blocked("SOURCE_PATH: traversal or symlink escape")
    current = root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            raise Blocked("SOURCE_PATH: symlinks are forbidden")
    return candidate


def run(argv: list[str], *, cwd: Path, timeout: int = 90) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Blocked(f"PROCESS: {exc}") from exc
    if result.returncode:
        err = (result.stderr or result.stdout).strip()
        raise Blocked(f"PROCESS: exit={result.returncode}: {err[-750:]}")
    return result


def checked_manifest(path: Path) -> dict:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise Blocked(f"MANIFEST: {exc}") from exc
    if not isinstance(obj, dict) or obj.get("schema") != SCHEMA:
        raise Blocked("MANIFEST: unknown schema")
    for key in ("source", "source_git_blob_sha1", "source_sha256",
                "expected_physical_sha256", "expected_typed_sha256"):
        value = obj.get(key)
        if not isinstance(value, str) or not value:
            raise Blocked(f"MANIFEST: missing {key}")
    for key, length in (("source_git_blob_sha1", 40), ("source_sha256", 64),
                        ("expected_physical_sha256", 64), ("expected_typed_sha256", 64)):
        value = obj[key]
        if len(value) != length or any(c not in "0123456789abcdef" for c in value):
            raise Blocked(f"MANIFEST: invalid {key}")
    if obj.get("source_era") != "historical-legacy":
        raise Blocked("SOURCE_ERA: current D8 and mixed-era calls require separate admitted law")
    tests = obj.get("oracle_commands")
    if not isinstance(tests, list) or not tests:
        raise Blocked("ORACLE: at least one independently admitted test command required")
    for argv in tests:
        if not isinstance(argv, list) or not argv or any(
            not isinstance(x, str) or not x for x in argv
        ):
            raise Blocked("ORACLE: argv must be a list of nonempty strings")
    return obj


def ensure_tracked(root: Path, source: Path, blob_sha: str) -> None:
    result = run(["git", "ls-files", "--stage", "--", source.as_posix()], cwd=root)
    entries = [line for line in result.stdout.splitlines() if "\t" in line]
    if len(entries) != 1:
        raise Blocked("SOURCE_PROVENANCE: original .lisp is not a single tracked file")
    stage_info, path = entries[0].split("\t", 1)
    fields = stage_info.split()
    if path != source.as_posix() or len(fields) != 3 or fields[0] != "100644":
        raise Blocked("SOURCE_PROVENANCE: source is not a regular stage-0 tracked file")
    if fields[1] != blob_sha or fields[2] != "0":
        raise Blocked("SOURCE_PROVENANCE: source diverges from pinned tracked Git blob")


def no_symlink_ancestors(path: Path, base: Path) -> None:
    cur = base
    for part in path.relative_to(base).parts:
        cur = cur / part
        if cur.is_symlink():
            raise Blocked("DESTINATION: symlink path is forbidden")


def publish(target: Path, payload: bytes, mirror: Path) -> None:
    no_symlink_ancestors(target, mirror)
    target.parent.mkdir(parents=True, exist_ok=True)
    no_symlink_ancestors(target, mirror)
    if target.exists() or target.is_symlink():
        raise Blocked("DESTINATION: existing .sens must never be overwritten")
    staged_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=".t5-proof-", delete=False
        ) as staged:
            staged_name = Path(staged.name)
            staged.write(payload)
            staged.flush()
            os.fsync(staged.fileno())
        try:
            os.link(staged_name, target)
        except FileExistsError as exc:
            raise Blocked("DESTINATION: existing .sens must never be overwritten") from exc
    finally:
        if staged_name:
            staged_name.unlink(missing_ok=True)


def admit(root: Path, mirror: Path, manifest: dict, reader: Path, write: bool) -> dict:
    root = root.resolve(strict=True)
    mirror = mirror.resolve(strict=False)
    if not root.is_dir() or not reader.is_file() or reader.is_symlink():
        raise Blocked("SETUP: repository root and real sens-trit reader are required")
    source = inside_root(root, manifest["source"])
    src_path = root / source
    if not src_path.is_file():
        raise Blocked("SOURCE: missing original tracked .lisp")
    src = src_path.read_bytes()
    blob = git_blob_sha(src)
    if blob != manifest["source_git_blob_sha1"] or digest(src) != manifest["source_sha256"]:
        raise Blocked("SOURCE_PROVENANCE: source SHA digest changed")
    ensure_tracked(root, source, blob)

    target = mirror / source.with_suffix(".sens")
    if target.exists() or target.is_symlink():
        raise Blocked("DESTINATION: existing .sens must never be overwritten")
    if mirror.exists() and mirror.is_symlink():
        raise Blocked("DESTINATION: symlink mirror forbidden")
    if not target.resolve().is_relative_to(mirror):
        raise Blocked("DESTINATION: mirror escape")

    with tempfile.TemporaryDirectory(prefix="sens-t5-proof-") as tmp:
        work = Path(tmp)
        isolated = work / "source"
        candidate = isolated / source
        candidate.parent.mkdir(parents=True)
        candidate.write_bytes(src)
        output = work / "out"
        report = work / "migration.json"
        command = [
            sys.executable, str(root / "scripts/migrate-three-pass.py"),
            str(isolated), "--out", str(output),
        ]
        for flag, artifact in ARTIFACTS.items():
            command.extend(["--" + flag, str(root / artifact)])
        command.extend(["--report", str(report)])
        run(command, cwd=root, timeout=120)
        status = json.loads(report.read_text(encoding="utf-8"))
        if (status["summary"]["files_seen"] != 1 or
            status["summary"]["files_written"] != 1 or
            status["summary"]["files_blocked"] != 0):
            raise Blocked("MIGRATION: not exactly one admitted legacy program")
        payload = (output / source.with_suffix(".sens")).read_bytes()
        words = decode_bytes(payload)
        if not words or encode_projection(" ".join(words)) != payload:
            raise Blocked("PHYSICAL: noncanonical T5 or lost exact word boundary")
        if digest(payload) != manifest["expected_physical_sha256"]:
            raise Blocked("PHYSICAL: candidate physical SHA differs from pinned proof")
        if typed_sha256(words) != manifest["expected_typed_sha256"]:
            raise Blocked("IDENTITY: typed word digest differs from pinned proof")
        opened = run([str(reader), "open", str(output / source.with_suffix(".sens"))],
                     cwd=root, timeout=30)
        if opened.stdout != " ".join(words) + "\n":
            raise Blocked("D2_GRAMMAR: Rust reader projection differs from typed T5 words")

        # The manifest supplies commands approved/reviewed by the repository,
        # not dynamic program meaning. Each command must pass independently.
        for oracle in manifest["oracle_commands"]:
            run(oracle, cwd=root, timeout=240)

        if write:
            publish(target, payload, mirror)
        return {
            "schema": SCHEMA,
            "status": "WRITTEN" if write else "VERIFIED_NOT_WRITTEN",
            "source": source.as_posix(),
            "target": str(target),
            "physical_bytes": len(payload),
            "source_git_blob_sha1": blob,
            "source_sha256": digest(src),
            "physical_sha256": digest(payload),
            "typed_sha256": typed_sha256(words),
            "d2_reader": "PASS",
            "oracle_commands_passed": len(manifest["oracle_commands"]),
            "warning": "Proof is bounded to named tests; not a general 491-file or release claim.",
        }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=REPO)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--mirror", type=Path, required=True)
    p.add_argument("--reader", type=Path, required=True)
    p.add_argument("--report", type=Path)
    p.add_argument("--write", action="store_true",
                   help="explicit publication after all proof gates pass (default dry run)")
    args = p.parse_args(argv)
    try:
        result = admit(
            args.root, args.mirror, checked_manifest(args.manifest),
            args.reader.resolve(strict=True), args.write,
        )
        code = 0
    except (Blocked, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        result = {"schema": SCHEMA, "status": "BLOCKED", "reason": str(exc)}
        code = 2
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
