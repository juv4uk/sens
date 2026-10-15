#!/usr/bin/env python3
"""#5767: exact Git-tracked manifest-path and SHA receipt regressions, no SENS semantics."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import subprocess
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/zig-codecs/tools/t5_corpus_snapshot.py"
SPEC = importlib.util.spec_from_file_location("t5_corpus_snapshot", SOURCE)
assert SPEC is not None and SPEC.loader is not None
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


class ExactManifestPaths(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="sens-t5-path-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "repo"
        self.root.mkdir()
        self.names = self.base / "parity_accept.txt"
        self.manifest = self.base / "snapshot.json"

    def file(self, name: str, payload: bytes = b"\x51") -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return path

    def listing(self, *names: str, crlf: bool = False) -> None:
        delimiter = "\r\n" if crlf else "\n"
        self.names.write_bytes((delimiter.join(names) + delimiter).encode("utf-8"))

    def test_exact_names_spaces_hash_and_unicode_separator(self) -> None:
        names = (" leading.sens", "trailing .sens", "#hash.sens", "unicode\u2028separator.sens")
        for index, name in enumerate(names):
            self.file(name, bytes([0x51 + index]))
        self.listing(*names)
        current = snapshot.snapshot(self.root, self.names)
        self.assertEqual({row["path"] for row in current["files"]}, set(names))
        self.assertEqual(current["count"], 4)
        self.assertEqual(len(current["corpus_sha256"]), 64)

    def test_crlf_and_lf_produce_same_corpus_sha(self) -> None:
        self.file(" leading.sens")
        self.file("#hash.sens", b"\x52")
        self.listing(" leading.sens", "#hash.sens", crlf=True)
        crlf = snapshot.snapshot(self.root, self.names)
        self.listing(" leading.sens", "#hash.sens")
        lf = snapshot.snapshot(self.root, self.names)
        self.assertEqual(crlf, lf)

    def test_duplicate_manifest_path_rejected(self) -> None:
        self.file("same.sens")
        self.listing("same.sens", "same.sens")
        with self.assertRaisesRegex(snapshot.SnapshotError, "duplicate:"):
            snapshot.snapshot(self.root, self.names)

    def test_missing_and_empty_manifest_rejected(self) -> None:
        self.listing("absent.sens")
        with self.assertRaisesRegex(snapshot.SnapshotError, "missing-file:"):
            snapshot.snapshot(self.root, self.names)
        self.names.write_bytes(b"")
        with self.assertRaisesRegex(snapshot.SnapshotError, "empty-corpus"):
            snapshot.snapshot(self.root, self.names)

    def test_symlink_is_not_a_physical_corpus_file(self) -> None:
        self.file("actual.sens")
        (self.root / "alias.sens").symlink_to(self.root / "actual.sens")
        self.listing("alias.sens")
        with self.assertRaisesRegex(snapshot.SnapshotError, "symlink:"):
            snapshot.snapshot(self.root, self.names)

    def test_escape_outside_repository_rejected(self) -> None:
        outside = self.base / "outside.sens"
        outside.write_bytes(b"\x51")
        self.listing("../outside.sens")
        with self.assertRaisesRegex(snapshot.SnapshotError, "outside-repository:"):
            snapshot.snapshot(self.root, self.names)

    def test_sha_receipt_detects_changed_bytes(self) -> None:
        target = self.file("actual.sens", b"\x51\x02")
        self.listing("actual.sens")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(snapshot.run(self.root, self.names, self.manifest, "write"), 0)
            self.assertEqual(snapshot.run(self.root, self.names, self.manifest, "check"), 0)
        target.write_bytes(b"\x51")  # valid shorter T5 can still be wrong corpus
        with redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(snapshot.run(self.root, self.names, self.manifest, "check"), 1)
        self.assertIn("layer=transport", stderr.getvalue())
        self.assertIn("first_diff=changed:actual.sens:bytes,sha256", stderr.getvalue())

    def test_manifest_digest_tampering_rejected(self) -> None:
        self.file("actual.sens")
        self.listing("actual.sens")
        with redirect_stdout(io.StringIO()):
            snapshot.run(self.root, self.names, self.manifest, "write")
        content = json.loads(self.manifest.read_text(encoding="utf-8"))
        content["corpus_sha256"] = "0" * 64
        self.manifest.write_text(json.dumps(content), encoding="utf-8")
        with self.assertRaisesRegex(snapshot.SnapshotError, "invalid-manifest-digest"):
            snapshot.run(self.root, self.names, self.manifest, "check")


    def test_strict_git_index_exact_membership_and_missing_or_untracked(self) -> None:
        self.file(" leading.sens")
        self.file("#unicode\u2028file.sens", b"\x52")
        self.file("untracked.sens", b"\x53")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "add", "--", " leading.sens", "#unicode\u2028file.sens"],
            cwd=self.root, check=True,
        )
        self.listing(" leading.sens", "#unicode\u2028file.sens")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                snapshot.run(self.root, self.names, self.manifest, "write",
                             require_git_index=True), 0,
            )
            self.assertEqual(
                snapshot.run(self.root, self.names, self.manifest, "check",
                             require_git_index=True), 0,
            )

        self.listing(" leading.sens")
        with self.assertRaisesRegex(snapshot.SnapshotError, "git-index-mismatch:missing="):
            snapshot.run(self.root, self.names, self.manifest, "check",
                         require_git_index=True)
        self.listing(" leading.sens", "#unicode\u2028file.sens", "untracked.sens")
        with self.assertRaisesRegex(snapshot.SnapshotError, "untracked=.*untracked.sens"):
            snapshot.run(self.root, self.names, self.manifest, "check",
                         require_git_index=True)

    def test_strict_git_index_requires_repository(self) -> None:
        self.file("standalone.sens")
        self.listing("standalone.sens")
        with self.assertRaisesRegex(snapshot.SnapshotError, "git-index-unavailable"):
            snapshot.run(self.root, self.names, self.manifest, "write",
                         require_git_index=True)


if __name__ == "__main__":
    unittest.main()
