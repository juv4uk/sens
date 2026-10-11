#!/usr/bin/env python3
"""Read-only plan, explicitly staged rehearsal and byte-exact audit of SENS T5/F3.

No automatic production cutover, no changing original .sens files, no
textual-domain migrations, no branch creation, no decoding by sniffing bytes.
This only orchestrates the repository's one reviewed Rust codec example.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNNER = ROOT / "target/release/examples/two_codec_small_programs"
SCHEMA = "sens-two-codec-migration-rehearsal/v1"


class Blocked(RuntimeError):
    pass


def command(args: list[str], *, cwd: Path = ROOT) -> str:
    p = subprocess.run(args, cwd=cwd, check=False, capture_output=True, text=True)
    if p.returncode:
        raise Blocked(f"command failed ({p.returncode}) {args[:2]!r}: "
                      f"{p.stderr[-1600:]}")
    return p.stdout


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(relative: str) -> Path:
    p = Path(relative)
    if p.is_absolute() or not relative or any(c in ("\t", "\n", "\r") for c in relative):
        raise Blocked(f"unsafe tracked file name: {relative!r}")
    if ".." in p.parts or p.suffix != ".sens":
        raise Blocked(f"non-T5 or escaping input: {relative!r}")
    source = ROOT / p
    if source.is_symlink() or not source.is_file() or not source.resolve().is_relative_to(ROOT):
        raise Blocked(f"non-regular or escaping tracked file: {relative}")
    return source


def tracked_files() -> list[str]:
    raw = subprocess.run(["git", "ls-files", "-z", "--", "*.sens"],
                         cwd=ROOT, capture_output=True, check=True).stdout
    files = [p.decode("utf-8") for p in raw.split(b"\x00") if p]
    if not files or files != sorted(set(files)):
        raise Blocked("empty, unsorted or duplicate T5 tracked file inventory")
    for name in files:
        safe_path(name)
    return files


def checked_runner(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise Blocked(f"missing verified Rust example binary: {path}; "
                      "build with cargo build --locked --release -p sens "
                      "--example two_codec_small_programs")
    return str(path.resolve())


def plan(runner: str) -> dict:
    tracked = tracked_files()
    raw = command([runner, "--report"])
    data = [x for x in raw.splitlines() if x and not x.startswith("#")]
    expected_header = (
        "file\tt5_bytes\tcodec\tselected_bytes\textension\t"
        "reason\tverified_f3_bytes"
    )
    if not data or data.pop(0) != expected_header:
        raise Blocked("Rust selector report header/protocol changed")
    found: dict[str, dict] = {}
    for line in data:
        fields = line.split("\t")
        if len(fields) != 7:
            raise Blocked("malformed or ambiguous selector TSV")
        name, t5_size, codec, selected_size, extension, reason, maybe_f3 = fields
        if name in found or name not in tracked:
            raise Blocked(f"unexpected duplicate/extra file from Rust report: {name}")
        if codec not in ("T5", "F3") or extension != (".sens" if codec == "T5" else ".senc"):
            raise Blocked(f"unknown selection/extension: {name}")
        if codec == "F3" and (reason != "F3_SMALLER_VERIFIED"
                              or int(selected_size) >= int(t5_size)
                              or int(t5_size) > 16
                              or maybe_f3 != selected_size):
            raise Blocked(f"unsafe F3 choice: {name}")
        if codec == "T5" and int(selected_size) != int(t5_size):
            raise Blocked(f"unexpected T5 size: {name}")
        source = safe_path(name)
        file_bytes = source.read_bytes()
        if len(file_bytes) != int(t5_size):
            raise Blocked(f"source size mismatch: {name}")
        selected_relative = str(Path(name).with_suffix(extension))
        if selected_relative in (row["staged_file"] for row in found.values()):
            raise Blocked(f"staged file collision: {selected_relative}")
        found[name] = {
            "source": name,
            "source_bytes": len(file_bytes),
            "source_sha256": digest(file_bytes),
            "codec": codec,
            "staged_file": selected_relative,
            "selected_bytes": int(selected_size),
            "reason": reason,
        }
    if sorted(found) != tracked:
        raise Blocked(f"Rust report missing tracked files: {set(tracked) - set(found)}")
    head = command(["git", "rev-parse", "HEAD"]).strip()
    rows = [found[name] for name in tracked]
    return {
        "schema": SCHEMA,
        "source_git_sha": head,
        "mode": "READ_ONLY_PLAN_NOT_DEPLOYED",
        "default_codec": "T5",
        "tiny_codec": "original-F3-0xf3",
        "tiny_baseline_max_t5_bytes": 16,
        "source_files": len(rows),
        "selected_f3": sum(x["codec"] == "F3" for x in rows),
        "selected_t5": sum(x["codec"] == "T5" for x in rows),
        "t5_total_bytes": sum(x["source_bytes"] for x in rows),
        "planned_total_bytes": sum(x["selected_bytes"] for x in rows),
        "files": rows,
    }


def validate_stage(stage: Path, runner: str, manifest: dict) -> None:
    if manifest.get("schema") != SCHEMA:
        raise Blocked("unknown migration manifest schema")
    if manifest.get("source_git_sha") != command(["git", "rev-parse", "HEAD"]).strip():
        raise Blocked("source HEAD has changed since plan: regenerate rehearsal")
    reference = plan(runner)
    if {k: v for k, v in manifest.items() if k != "mode"} != {
        k: v for k, v in reference.items() if k != "mode"
    }:
        # The staged variant adds output hashes to rows; compare below instead.
        planned_rows = [{k: v for k, v in r.items() if k != "staged_sha256"}
                        for r in manifest.get("files", [])]
        if planned_rows != reference["files"] or any(
            manifest.get(k) != v for k, v in reference.items() if k not in ("files", "mode")
        ):
            raise Blocked("manifest and fresh current-head Rust selector disagree")
    expected_files = {"manifest.json"}
    for row in manifest["files"]:
        source = safe_path(row["source"])
        original = source.read_bytes()
        if digest(original) != row["source_sha256"] or len(original) != row["source_bytes"]:
            raise Blocked(f"source mutated: {row['source']}")
        target_relative = row["staged_file"]
        expected_files.add(target_relative)
        output = stage / target_relative
        if output.is_symlink() or not output.is_file() or not output.resolve().is_relative_to(stage):
            raise Blocked(f"missing, symlinked or escaping staged artifact: {target_relative}")
        payload = output.read_bytes()
        if len(payload) != row["selected_bytes"] or digest(payload) != row.get("staged_sha256"):
            raise Blocked(f"staged hash/size mismatch: {target_relative}")
        if row["codec"] == "F3" and (not payload or payload[0] != 0xf3):
            raise Blocked(f"wrong F3 marker: {target_relative}")
        with tempfile.TemporaryDirectory(prefix="sens-rehearsal-verify-") as scratch:
            stem = Path(scratch) / "restored"
            command([runner, "--restore", str(output), str(stem)])
            recovered = stem.with_suffix(".sens").read_bytes()
            if recovered != original:
                raise Blocked(f"physical T5 was not restored exactly: {target_relative}")
    actual_files = set()
    for p in stage.rglob("*"):
        if p.is_symlink():
            raise Blocked(f"unexpected symlink in stage: {p}")
        if p.is_file():
            actual_files.add(p.relative_to(stage).as_posix())
    if actual_files != expected_files:
        raise Blocked(f"stage missing/contains extra files: "
                      f"missing={expected_files - actual_files} extra={actual_files - expected_files}")


def stage_plan(stage: Path, runner: str, manifest: dict) -> dict:
    if stage.exists() or stage.is_symlink():
        raise Blocked(f"refuse existing staging destination: {stage}")
    if stage.resolve().is_relative_to(ROOT):
        raise Blocked("staging destination must be OUTSIDE the Git repository")
    stage.mkdir(parents=True, exist_ok=False)
    try:
        for row in manifest["files"]:
            output = stage / row["staged_file"]
            output.parent.mkdir(parents=True, exist_ok=True)
            source = safe_path(row["source"])
            if digest(source.read_bytes()) != row["source_sha256"]:
                raise Blocked(f"source changed during migration rehearsal: {row['source']}")
            stem = output.with_suffix("")
            command([runner, "--convert", str(source), str(stem)])
            staged = output.read_bytes()
            if len(staged) != row["selected_bytes"]:
                raise Blocked(f"Rust staged wrong size: {output}")
            row["staged_sha256"] = digest(staged)
        manifest["mode"] = "STAGED_NOT_DEPLOYED"
        with (stage / "manifest.json").open("x", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        validate_stage(stage, runner, manifest)
    except BaseException:
        # Do not remove diagnostic partial outputs or overwrite existing data.
        # They remain outside the repository, and no cutover took place.
        raise
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--stage", type=Path, metavar="OUTSIDE_REPO_DIR",
                       help="create-new separately staged files; NEVER deploy")
    group.add_argument("--verify-stage", type=Path, metavar="EXISTING_DIR",
                       help="audit manifest and independently restore every physical file")
    parser.add_argument("--runner", type=Path, default=DEFAULT_RUNNER,
                        help="previously built Rust example binary")
    args = parser.parse_args()
    try:
        runner = checked_runner(args.runner)
        if args.verify_stage:
            stage = args.verify_stage.resolve()
            if not stage.is_dir() or stage.is_symlink() or stage.is_relative_to(ROOT):
                raise Blocked("verification needs non-symlink stage outside repository")
            manifest = json.loads((stage / "manifest.json").read_text(encoding="utf-8"))
            validate_stage(stage, runner, manifest)
            print("TWO_CODEC_STAGE_VERIFIED: all files, exact bytes, sources and SHA", file=sys.stderr)
        elif args.stage:
            stage = args.stage.absolute()
            manifest = stage_plan(stage, runner, plan(runner))
            print("TWO_CODEC_STAGED_NOT_DEPLOYED: exact restores all PASS", file=sys.stderr)
        else:
            manifest = plan(runner)
            print("TWO_CODEC_DRY_RUN: inventory only; no source files changed", file=sys.stderr)
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (Blocked, ValueError, OSError, subprocess.SubprocessError) as e:
        print(f"TWO_CODEC_MIGRATION_BLOCKED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
