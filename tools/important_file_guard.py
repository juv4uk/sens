#!/usr/bin/env python3
"""Mechanical Git-path transport for the SENS-owned file-authority oracle.

No admission policy, census parsing, violation classification, asserts, or shell
commands live here. It supplies exact Git path facts and packages the executable
SENS law as source so CI can encode it to physical T5 and run the .sens file.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SHA1 = re.compile(r"^[0-9a-f]{40}$")


class TransportError(ValueError):
    """Named fail-closed error at the untrusted Git transport boundary."""


def fail(message: str) -> None:
    raise TransportError(message)


def git(*args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        fail(f"GIT_COMMAND_FAILED returncode={result.returncode} args={args!r} stderr={detail}")
    return result.stdout


def nul_paths(data: bytes) -> list[str]:
    if not data:
        return []
    if not data.endswith(b"\x00"):
        fail("UNTERMINATED_GIT_NUL_STREAM")
    pieces = data[:-1].split(b"\x00")
    if any(not piece for piece in pieces):
        fail("EMPTY_FIELD_IN_GIT_NUL_STREAM")
    try:
        return [piece.decode("utf-8", "strict") for piece in pieces]
    except UnicodeDecodeError as error:
        fail(f"GIT_PATH_ENCODING_INVALID: {error}")


def introduced_paths(data: bytes) -> list[str]:
    """Return add/rename/copy destinations from Git's NUL name-status stream."""
    if data and not data.endswith(b"\x00"):
        fail("UNTERMINATED_GIT_NAME_STATUS")
    fields = data[:-1].split(b"\x00") if data else []
    found: list[str] = []
    offset = 0
    while offset < len(fields):
        try:
            status = fields[offset].decode("ascii", "strict")
        except UnicodeDecodeError as error:
            fail(f"GIT_STATUS_ENCODING_INVALID: {error}")
        offset += 1
        if status == "A":
            if offset >= len(fields):
                fail("GIT_STATUS_TRUNCATED_ADDITION")
            destination = fields[offset]
            offset += 1
        elif status.startswith(("R", "C")) and status[1:].isdigit():
            if offset + 1 >= len(fields):
                fail("GIT_STATUS_TRUNCATED_RENAME_OR_COPY")
            destination = fields[offset + 1]
            offset += 2
        else:
            fail(f"GIT_STATUS_UNEXPECTED_CHANGE: {status}")
        try:
            found.append(destination.decode("utf-8", "strict"))
        except UnicodeDecodeError as error:
            fail(f"GIT_PATH_ENCODING_INVALID: {error}")
    return found


def typechanged_paths(data: bytes) -> list[str]:
    """Decode Git T-status records; a type change is not a newly added path."""
    if data and not data.endswith(b"\x00"):
        fail("UNTERMINATED_GIT_TYPE_CHANGE")
    fields = data[:-1].split(b"\x00") if data else []
    found: list[str] = []
    offset = 0
    while offset < len(fields):
        try:
            status = fields[offset].decode("ascii", "strict")
        except UnicodeDecodeError as error:
            fail(f"GIT_TYPE_CHANGE_STATUS_ENCODING_INVALID: {error}")
        offset += 1
        if status != "T":
            fail(f"GIT_TYPE_CHANGE_UNEXPECTED_STATUS: {status}")
        if offset >= len(fields):
            fail("GIT_TYPE_CHANGE_TRUNCATED_PATH")
        try:
            path = fields[offset].decode("utf-8", "strict")
        except UnicodeDecodeError as error:
            fail(f"GIT_PATH_ENCODING_INVALID: {error}")
        if not path:
            fail("GIT_TYPE_CHANGE_EMPTY_PATH")
        found.append(path)
        offset += 1
    return found


def lisp_string(value: str) -> str:
    # Git permits newlines/control characters in paths; the SENS source carrier
    # intentionally refuses them instead of emitting ambiguous Lisp source.
    for character in value:
        codepoint = ord(character)
        if codepoint < 32 or codepoint == 127:
            fail(f"UNREPRESENTABLE_CONTROL_CHARACTER_IN_GIT_PATH: U+{codepoint:04X}")
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + escaped + '"'


def lisp_list(values: list[str]) -> str:
    return "(" + " ".join(lisp_string(value) for value in values) + ")"


def git_path_mode(head: str, path: str) -> str:
    """An exact Git mode/type fact; SENS, not this adapter, decides admission."""
    record = git("ls-tree", "-z", "--full-tree", head, "--", path)
    if record.count(b"\x00") != 1 or not record.endswith(b"\x00"):
        fail("GIT_MODE_RECORD_MISSING_OR_TRUNCATED: " + path)
    row = record[:-1]
    if row.count(b"\t") != 1:
        fail("GIT_MODE_RECORD_MALFORMED: " + path)
    meta, encoded_path = row.split(b"\t", 1)
    fields = meta.split(b" ")
    if len(fields) != 3 or encoded_path.decode("utf-8", "strict") != path:
        fail("GIT_MODE_PATH_MISMATCH: " + path)
    mode, kind, oid = fields
    if len(oid) not in (40, 64) or not re.fullmatch(rb"[0-9a-f]+", oid):
        fail("GIT_MODE_OBJECT_ID_INVALID: " + path)
    return mode.decode("ascii", "strict") + ":" + kind.decode("ascii", "strict")


def read_head_source(head: str, path: str) -> str | None:
    """Read a single exact regular source blob from the audited commit, not checkout."""
    record = git("ls-tree", "-z", "--full-tree", head, "--", path)
    if not record:
        return None
    if record.count(b"\x00") != 1 or not record.endswith(b"\x00"):
        fail("INVALID_GIT_SOURCE_TREE_RECORD: " + path)
    row = record[:-1]
    if row.count(b"\t") != 1:
        fail("INVALID_GIT_SOURCE_TREE_FIELDS: " + path)
    metadata, recorded_path = row.split(b"\t", 1)
    parts = metadata.split(b" ")
    if len(parts) != 3 or recorded_path.decode("utf-8", "strict") != path:
        fail("GIT_SOURCE_PATH_OR_METADATA_MISMATCH: " + path)
    mode, kind, oid = parts
    if len(oid) not in (40, 64) or not re.fullmatch(rb"[0-9a-f]+", oid):
        fail("INVALID_GIT_SOURCE_OBJECT_ID: " + path)
    if mode not in (b"100644", b"100755") or kind != b"blob":
        fail("NON_REGULAR_GIT_SOURCE: " + path)
    return git("show", f"{head}:{path}").decode("utf-8", "strict")


def path_status(name: str, value: str | None) -> str:
    return f"({name} . {'present' if value is not None else 'missing'})"


def input_form(
    added: list[str],
    tracked_tools: list[str],
    modes: list[tuple[str, str]],
    typechanged: list[str],
    typechanged_modes: list[tuple[str, str]],
) -> str:
    mode_rows = "(" + " ".join(
        "(" + lisp_string(path) + " . " + lisp_string(mode) + ")"
        for path, mode in modes
    ) + ")"
    typechanged_mode_rows = "(" + " ".join(
        "(" + lisp_string(path) + " . " + lisp_string(mode) + ")"
        for path, mode in typechanged_modes
    ) + ")"
    return (
        "(00001001 *file-authority-input*\n"
        "  (00000001\n"
        "    ((schema . file-authority-input/1)\n"
        f"     (added-paths . {lisp_list(added)})\n"
        f"     (added-modes . {mode_rows})\n"
        f"     (typechanged-paths . {lisp_list(typechanged)})\n"
        f"     (typechanged-modes . {typechanged_mode_rows})\n"
        f"     (tracked-tools-paths . {lisp_list(tracked_tools)}))))\n"
    )


def status_form(policy: str | None, census: str | None, guard: str | None) -> str:
    return (
        "(00001001 *file-authority-source-status*\n"
        "  (00000001\n"
        "    ("
        + path_status("policy", policy)
        + " "
        + path_status("census", census)
        + " "
        + path_status("guard", guard)
        + ")))\n"
    )


def fail_program(reason: str) -> str:
    # This is itself SENS code. The missing source is reported as an unresolved
    # named SENS call, so the physical evaluator exits non-zero without fallback.
    return f"(sens_file_authority_source_missing_5397_{reason})\n"


def build_bundle(
    added: list[str],
    tracked_tools: list[str],
    modes: list[tuple[str, str]],
    typechanged: list[str],
    typechanged_modes: list[tuple[str, str]],
    head: str,
) -> str:
    core = read_head_source(head, "lib/core.lisp")
    policy = read_head_source(head, "knowledge/file-authority-policy.lisp")
    census = read_head_source(head, "knowledge/foreign-tools-census.lisp")
    guard = read_head_source(head, "knowledge/file-authority-guard.lisp")

    if core is None:
        return fail_program("core")
    if guard is None:
        return fail_program("guard")

    parts = [core]
    if policy is not None:
        parts.append(policy)
    if census is not None:
        parts.append(census)
    parts.append(status_form(policy, census, guard))
    parts.append(input_form(added, tracked_tools, modes, typechanged, typechanged_modes))
    parts.append(guard)
    return "\n\n".join(parts) + "\n"


def expect(label: str, actual: object, expected: object) -> None:
    if actual != expected:
        fail(f"TRANSPORT_SELF_TEST_FAILED {label}: actual={actual!r} expected={expected!r}")


def catches(callback) -> bool:
    try:
        callback()
    except (TransportError, UnicodeError):
        return True
    return False


def self_test() -> None:
    expect("empty-NUL-stream", nul_paths(b""), [])
    expect("valid-NUL-stream", nul_paths(b"tools/a.py\x00"), ["tools/a.py"])
    expect(
        "rename-destination",
        introduced_paths(b"R100\x00docs/old.json\x00knowledge/new.json\x00"),
        ["knowledge/new.json"],
    )
    expect(
        "copy-destination",
        introduced_paths(b"C100\x00tools/old.py\x00tools/new.py\x00"),
        ["tools/new.py"],
    )
    expect(
        "type-change-is-separate-from-addition",
        typechanged_paths(bytes.fromhex("54006c69622f73616d706c652e73656e7300")),
        ["lib/sample.sens"],
    )
    for malformed in (
        bytes.fromhex("54006c69622f73616d706c652e73656e73"),
        bytes.fromhex("5400"),
        bytes.fromhex("4d006c69622f73616d706c652e73656e7300"),
        bytes.fromhex("54006c69622f73616d706c652e73656e730054"),
    ):
        if not catches(lambda malformed=malformed: typechanged_paths(malformed)):
            fail("TRANSPORT_SELF_TEST_ACCEPTED_MALFORMED_TYPE_CHANGE")
    encoded_typechange_input = input_form(
        [], [], [], ["lib/sample.sens"], [("lib/sample.sens", "120000:blob")]
    )
    expect("type-change-path-is-transported-separately",
           "typechanged-paths" in encoded_typechange_input, True)
    expect("type-change-mode-is-transported-separately",
           "120000:blob" in encoded_typechange_input, True)
    expect("UTF8-path", nul_paths("knowledge/дані.sens".encode("utf-8") + b"\x00"),
           ["knowledge/дані.sens"])
    if not catches(lambda: nul_paths(b"unterminated")):
        fail("TRANSPORT_SELF_TEST_ACCEPTED_UNTERMINATED_NUL_STREAM")
    if not catches(lambda: nul_paths(b"\xff\x00")):
        fail("TRANSPORT_SELF_TEST_ACCEPTED_NON_UTF8_PATH")
    expect("Lisp-escaping", lisp_string('a"b\\c'), '"a\\"b\\\\c"')
    if not catches(lambda: lisp_string("unsafe\x01path")):
        fail("TRANSPORT_SELF_TEST_ACCEPTED_CONTROL_CHARACTER")
    # Real Git regression: --diff-filter=ACR misses T; --diff-filter=T finds symlink swap.
    with tempfile.TemporaryDirectory(prefix="sens-typechange-") as temporary:
        root = Path(temporary)
        subprocess.run(["git", "init", "-q", str(root)], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (root / "lib").mkdir()
        sample = root / "lib" / "sample.sens"
        target = root / "lib" / "target.bin"
        sample.write_bytes(b"physical-source")
        target.write_bytes(b"symlink-target")
        subprocess.run(
            ["git", "-C", str(root), "add", "--", "lib/sample.sens", "lib/target.bin"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        base_tree = subprocess.run(
            ["git", "-C", str(root), "write-tree"], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout.decode("ascii", "strict").strip()
        sample.unlink()
        sample.symlink_to("target.bin")
        subprocess.run(["git", "-C", str(root), "add", "-A", "--", "lib/sample.sens"],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        head_tree = subprocess.run(
            ["git", "-C", str(root), "write-tree"], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout.decode("ascii", "strict").strip()
        acr_result = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-status", "-z",
             "--diff-filter=ACR", base_tree, head_tree],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        type_result = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-status", "-z",
             "--diff-filter=T", base_tree, head_tree],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        expect("real-Git-ACR-filter-misses-T", acr_result, b"")
        expect("real-Git-T-filter-finds-symlink-change",
               typechanged_paths(type_result), ["lib/sample.sens"])
        tree_record = subprocess.run(
            ["git", "-C", str(root), "ls-tree", "-z", "--full-tree",
             head_tree, "--", "lib/sample.sens"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        fields = tree_record[:-1].split(bytes([9]), 1)[0].split(b" ")
        mode = fields[0].decode("ascii") + ":" + fields[1].decode("ascii")
        expect("real-Git-symlink-mode", mode, "120000:blob")
        regular_record = subprocess.run(
            ["git", "-C", str(root), "ls-tree", "-z", "--full-tree",
             base_tree, "--", "lib/sample.sens"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        regular_fields = regular_record[:-1].split(bytes([9]), 1)[0].split(b" ")
        regular_mode = regular_fields[0].decode("ascii") + ":" + regular_fields[1].decode("ascii")
        expect("real-Git-original-regular-mode", regular_mode, "100644:blob")

    # Один точний Git tree, зіпсовані index і worktree: SENS отримує лише HEAD-факти.
    with tempfile.TemporaryDirectory(prefix="sens-head-ingress-") as temporary:
        root = Path(temporary)
        subprocess.run(["git", "init", "-q", str(root)], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (root / "knowledge").mkdir()
        (root / "tools").mkdir()
        census_path = "knowledge/foreign-tools-census.lisp"
        (root / census_path).write_text("census-з-HEAD", encoding="utf-8")
        (root / "tools" / "unlisted.py").write_text("foreign", encoding="utf-8")
        (root / "knowledge" / "symlink.lisp").symlink_to("foreign-tools-census.lisp")
        subprocess.run(
            ["git", "-C", str(root), "add", "--", census_path,
             "knowledge/symlink.lisp", "tools/unlisted.py"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        tree_sha = subprocess.run(
            ["git", "-C", str(root), "write-tree"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout.decode("ascii", "strict").strip()
        (root / census_path).write_text("підроблений робочий census", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "read-tree", "--empty"],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        previous_cwd = Path.cwd()
        try:
            os.chdir(root)
            expect("head-source-not-worktree",
                   read_head_source(tree_sha, census_path), "census-з-HEAD")
            exact_tools = nul_paths(git(
                "ls-tree", "-r", "-z", "--name-only", "--full-tree",
                tree_sha, "--", "tools/"))
            expect("head-tools-not-index", exact_tools, ["tools/unlisted.py"])
            expect("cleared-index", nul_paths(git("ls-files", "-z", "--", "tools/")), [])
            expect("head-regular-mode",
                   git_path_mode(tree_sha, census_path), "100644:blob")
            expect("head-symlink-mode",
                   git_path_mode(tree_sha, "knowledge/symlink.lisp"), "120000:blob")
            quoted = input_form(
                ["knowledge/symlink.lisp"], [],
                [("knowledge/symlink.lisp", "120000:blob")],
                [], [],
            )
            if '(added-modes . (("knowledge/symlink.lisp" . "120000:blob")))' not in quoted:
                fail("TRANSPORT_SELF_TEST_MISSING_GIT_MODE_INPUT")
            if not catches(lambda: git_path_mode(tree_sha, "knowledge/missing.lisp")):
                fail("TRANSPORT_SELF_TEST_ACCEPTED_MISSING_GIT_MODE")
            expect("missing-exact-source",
                   read_head_source(tree_sha, "knowledge/missing.lisp"), None)
            if not catches(lambda: read_head_source(tree_sha, "knowledge/symlink.lisp")):
                fail("TRANSPORT_SELF_TEST_ACCEPTED_SYMLINK_SOURCE")
        finally:
            os.chdir(previous_cwd)
    print("GIT_PATH_TRANSPORT_SELF_TEST_PASS: 9 mechanical checks; no policy verdict")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="exact PR-base or push-before commit SHA")
    parser.add_argument("--output", type=Path, help="temporary SENS source bundle")
    parser.add_argument("--self-test", action="store_true",
                        help="test only Git NUL framing and SENS string transport")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.base is None or args.output is None:
        fail("MISSING_BASE_OR_OUTPUT")
    if not SHA1.fullmatch(args.base) or set(args.base) == {"0"}:
        fail("INVALID_OR_MISSING_BASE_SHA")

    git("cat-file", "-e", f"{args.base}^{{commit}}")
    head = git("rev-parse", "--verify", "HEAD^{commit}").decode("ascii", "strict").strip()
    if not SHA1.fullmatch(head):
        fail("INVALID_HEAD_SHA")
    git("merge-base", "--is-ancestor", args.base, head)

    changes = git(
        "diff", "--name-status", "-z", "--diff-filter=ACR",
        "--find-renames", "--find-copies", "--find-copies-harder",
        args.base, head,
    )
    added = introduced_paths(changes)
    # T is separate from A/C/R: it must not enter the new-path extension policy.
    type_changes = git("diff", "--name-status", "-z", "--diff-filter=T", args.base, head)
    typechanged = typechanged_paths(type_changes)
    typechanged_modes = [(path, git_path_mode(head, path)) for path in typechanged]

    tracked_tools = nul_paths(git("ls-tree", "-r", "-z", "--name-only", "--full-tree", head, "--", "tools/"))
    modes = [(path, git_path_mode(head, path)) for path in added]
    bundle = build_bundle(added, tracked_tools, modes, typechanged, typechanged_modes, head)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(bundle.encode("utf-8", "strict"))
    print(
        "GIT_PATH_TRANSPORT_READY "
        f"base={args.base} head={head} added_paths={len(added)} "
        f"tracked_tools_paths={len(tracked_tools)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, TransportError, UnicodeError) as error:
        print(f"GIT_PATH_TRANSPORT_BLOCKED: {error}", file=sys.stderr)
        raise SystemExit(2)
