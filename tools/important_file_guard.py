#!/usr/bin/env python3
"""Mechanical Git-path transport for the SENS-owned file-authority oracle.

No admission policy, census parsing, violation classification, asserts, or shell
commands live here. It supplies exact Git path facts and packages the executable
SENS law as source so CI can encode it to physical T5 and run the .sens file.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
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


def read_optional(path: str) -> str | None:
    try:
        return Path(path).read_bytes().decode("utf-8", "strict")
    except FileNotFoundError:
        return None


def path_status(name: str, value: str | None) -> str:
    return f"({name} . {'present' if value is not None else 'missing'})"


def input_form(added: list[str], tracked_tools: list[str]) -> str:
    return (
        "(00001001 *file-authority-input*\n"
        "  (00000001\n"
        "    ((schema . file-authority-input/1)\n"
        f"     (added-paths . {lisp_list(added)})\n"
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


def build_bundle(added: list[str], tracked_tools: list[str]) -> str:
    core = read_optional("lib/core.lisp")
    policy = read_optional("knowledge/file-authority-policy.lisp")
    census = read_optional("knowledge/foreign-tools-census.lisp")
    guard = read_optional("knowledge/file-authority-guard.lisp")

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
    parts.append(input_form(added, tracked_tools))
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
    expect("UTF8-path", nul_paths("knowledge/дані.sens".encode("utf-8") + b"\x00"),
           ["knowledge/дані.sens"])
    if not catches(lambda: nul_paths(b"unterminated")):
        fail("TRANSPORT_SELF_TEST_ACCEPTED_UNTERMINATED_NUL_STREAM")
    if not catches(lambda: nul_paths(b"\xff\x00")):
        fail("TRANSPORT_SELF_TEST_ACCEPTED_NON_UTF8_PATH")
    expect("Lisp-escaping", lisp_string('a"b\\c'), '"a\\"b\\\\c"')
    if not catches(lambda: lisp_string("unsafe\x01path")):
        fail("TRANSPORT_SELF_TEST_ACCEPTED_CONTROL_CHARACTER")
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
    tracked_tools = nul_paths(git("ls-tree", "-r", "-z", "--name-only", "--full-tree", head, "--", "tools/"))
    bundle = build_bundle(added, tracked_tools)

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
