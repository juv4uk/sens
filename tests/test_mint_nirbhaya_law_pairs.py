"""Mechanical safety tests for the Nirbhaya canonical T5M pair builder.

These fake executables test command wiring, stale-archive avoidance and failure
atomicity only. They do not certify SENS semantics or replace native CI.
"""
from __future__ import annotations

import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mint-nirbhaya-law-pairs.py"
SPEC = importlib.util.spec_from_file_location("mint_nirbhaya_law_pairs", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import script under test: {SCRIPT}")
MINT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MINT)


FAKE_SENS = r'''#!/usr/bin/env python3
import os
import sys
from pathlib import Path

if len(sys.argv) != 4 or sys.argv[1] != "--t5m-mint":
    raise SystemExit("unexpected SENS arguments")
source = Path(sys.argv[2])
target = Path(sys.argv[3])
source_bytes = source.read_bytes()
target.write_bytes(b"T5M\\0" + source_bytes)

mutate_source = os.environ.get("NIRBHAYA_MUTATE_SOURCE")
mutate_marker = os.environ.get("NIRBHAYA_MUTATE_MARKER")
if mutate_source and mutate_marker and not Path(mutate_marker).exists():
    Path(mutate_marker).write_text("source mutation injected by test")
    Path(mutate_source).write_bytes(b"concurrent source mutation")

race_target = os.environ.get("NIRBHAYA_RACE_TARGET")
race_marker = os.environ.get("NIRBHAYA_RACE_MARKER")
if race_target and race_marker and not Path(race_marker).exists():
    Path(race_marker).write_text("target mutation injected by test")
    Path(race_target).write_bytes(b"concurrent target update")
'''


FAKE_TRIT = r'''#!/usr/bin/env python3
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("unexpected sens-trit arguments")
command, path = sys.argv[1:]
data = Path(path).read_bytes()
if command == "view":
    sys.stdout.buffer.write(b"VIEW:" + data)
elif command == "verify-view":
    if not data.startswith(b"T5M\\0"):
        raise SystemExit("invalid T5M test carrier")
else:
    raise SystemExit("unexpected sens-trit command")
'''


class NirbhayaMintPairsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="sens-nirbhaya-test-")
        self.root = Path(self.temp.name)
        self.semantic = self.root / "tests" / "semantic"
        self.semantic.mkdir(parents=True)
        self.archive = self.root / "knowledge" / "d11" / "restore" / "nirbhaya"
        self.archive.mkdir(parents=True)
        self.sens = self.root / "fake-sens"
        self.trit = self.root / "fake-sens-trit"
        self._write_executable(self.sens, FAKE_SENS)
        self._write_executable(self.trit, FAKE_TRIT)

        for index, stem in enumerate(MINT.STEMS):
            (self.semantic / f"{stem}.lisp").write_bytes(
                f"; current source {index}\\n".encode("utf-8")
            )
            # Deliberately stale data: the live helper must not restore this.
            (self.archive / f"{stem}.sens.b64").write_text("stale archive carrier")
            (self.archive / f"{stem}.view.b64").write_text("stale archive view")

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _write_executable(path: Path, source: str) -> None:
        path.write_text(source, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def _targets(self, stem: str) -> tuple[Path, Path]:
        return self.semantic / f"{stem}.sens", self.semantic / stem

    def _seed_old_targets(self) -> dict[Path, bytes]:
        old: dict[Path, bytes] = {}
        for stem in MINT.STEMS:
            for target in self._targets(stem):
                payload = b"old artifact:" + target.name.encode("utf-8")
                target.write_bytes(payload)
                old[target] = payload
        return old

    def test_pairs_are_minted_from_current_sources_not_archived_blobs(self) -> None:
        self._seed_old_targets()
        results = MINT.mint_all(self.root, self.sens, self.trit)

        self.assertEqual(len(results), len(MINT.STEMS))
        for stem in MINT.STEMS:
            source = (self.semantic / f"{stem}.lisp").read_bytes()
            physical, view = self._targets(stem)
            self.assertEqual(physical.read_bytes(), b"T5M\\0" + source)
            self.assertEqual(view.read_bytes(), b"VIEW:T5M\\0" + source)
        self.assertTrue(all("source_sha256" in row for row in results))

    def test_concurrent_target_change_aborts_before_any_pair_is_published(self) -> None:
        old = self._seed_old_targets()
        raced_target = self._targets(MINT.STEMS[0])[0]
        marker = self.root / "race-target.once"
        env = {
            "NIRBHAYA_RACE_TARGET": str(raced_target),
            "NIRBHAYA_RACE_MARKER": str(marker),
        }
        with patch.dict(os.environ, env, clear=False):
            with self.assertRaisesRegex(RuntimeError, "NIRBHAYA_CONCURRENT_TARGET_UPDATE"):
                MINT.mint_all(self.root, self.sens, self.trit)

        self.assertEqual(raced_target.read_bytes(), b"concurrent target update")
        for target, payload in old.items():
            if target != raced_target:
                self.assertEqual(target.read_bytes(), payload)

    def test_source_change_during_mint_aborts_without_publishing(self) -> None:
        old = self._seed_old_targets()
        source = self.semantic / f"{MINT.STEMS[0]}.lisp"
        marker = self.root / "race-source.once"
        env = {
            "NIRBHAYA_MUTATE_SOURCE": str(source),
            "NIRBHAYA_MUTATE_MARKER": str(marker),
        }
        with patch.dict(os.environ, env, clear=False):
            with self.assertRaisesRegex(RuntimeError, "NIRBHAYA_SOURCE_CHANGED_DURING_MINT"):
                MINT.mint_all(self.root, self.sens, self.trit)

        for target, payload in old.items():
            self.assertEqual(target.read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
