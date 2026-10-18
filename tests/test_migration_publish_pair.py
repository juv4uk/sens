"""Narrow positive/negative controls for same-stem carrier/view publication."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PUBLISHER = Path(__file__).resolve().parents[1] / "scripts/migration_publish_pair.py"
spec = importlib.util.spec_from_file_location("sens_migration_publish_pair", PUBLISHER)
assert spec and spec.loader
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class SameStemPublicationTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.carrier = self.root / "branch.sens"
        self.view = self.root / "branch"
        self.carrier_bytes = bytes.fromhex("6738")
        self.view_bytes = b"10 110 00\n"

    @staticmethod
    def write_new(path: Path, data: bytes) -> None:
        with path.open("xb") as stream:
            stream.write(data)

    def publish(self, writer=None):
        publisher.publish_pair(writer or self.write_new, self.carrier,
                               self.carrier_bytes, self.view, self.view_bytes)

    def test_success_keeps_exact_physical_and_readable_view(self):
        self.publish()
        self.assertEqual(self.carrier.read_bytes(), self.carrier_bytes)
        self.assertEqual(self.view.read_bytes(), self.view_bytes)
        self.assertTrue(self.view_bytes.endswith(bytes([10])))

    def test_existing_view_blocks_before_any_carrier_publication(self):
        self.view.write_bytes(b"existing")
        with self.assertRaisesRegex(FileExistsError, "PAIR_OUTPUT_EXISTS"):
            self.publish()
        self.assertEqual(self.view.read_bytes(), b"existing")
        self.assertFalse(self.carrier.exists())

    def test_existing_carrier_is_never_modified(self):
        self.carrier.write_bytes(b"existing carrier")
        with self.assertRaisesRegex(FileExistsError, "PAIR_OUTPUT_EXISTS"):
            self.publish()
        self.assertEqual(self.carrier.read_bytes(), b"existing carrier")
        self.assertFalse(self.view.exists())

    def test_second_write_failure_rolls_back_newly_created_carrier(self):
        def fails_view(path, data):
            if path == self.view:
                raise OSError("injected view failure")
            self.write_new(path, data)
        with self.assertRaisesRegex(OSError, "injected view failure"):
            self.publish(fails_view)
        self.assertFalse(self.carrier.exists())
        self.assertFalse(self.view.exists())

    def test_first_write_failure_does_not_touch_preexisting_view(self):
        def fails_carrier(path, data):
            raise OSError("injected carrier failure")
        with self.assertRaisesRegex(OSError, "injected carrier failure"):
            self.publish(fails_carrier)
        self.assertFalse(self.carrier.exists())
        self.assertFalse(self.view.exists())

    def test_replace_pair_refreshes_existing_same_stem_artifacts(self):
        self.carrier.write_bytes(b"stale carrier")
        self.view.write_bytes(b"stale view")
        publisher.replace_pair(self.carrier, self.carrier_bytes, self.view, self.view_bytes)
        self.assertEqual(self.carrier.read_bytes(), self.carrier_bytes)
        self.assertEqual(self.view.read_bytes(), self.view_bytes)

    def test_replace_pair_rolls_back_carrier_when_view_replace_fails(self):
        old_carrier, old_view = b"old carrier", b"old view"
        self.carrier.write_bytes(old_carrier)
        self.view.write_bytes(old_view)
        real_replace = publisher.os.replace
        calls = 0

        def fail_second_replace(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected second replace failure")
            return real_replace(source, target)

        with patch.object(publisher.os, "replace", side_effect=fail_second_replace):
            with self.assertRaisesRegex(OSError, "injected second replace failure"):
                publisher.replace_pair(self.carrier, self.carrier_bytes, self.view, self.view_bytes)
        self.assertEqual(self.carrier.read_bytes(), old_carrier)
        self.assertEqual(self.view.read_bytes(), old_view)

    def test_replace_pair_rejects_symlink_before_publication(self):
        target = self.root / "outside"
        target.write_bytes(b"outside bytes")
        self.view.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "PAIR_OUTPUT_SYMLINK"):
            publisher.replace_pair(self.carrier, self.carrier_bytes, self.view, self.view_bytes)
        self.assertFalse(self.carrier.exists())
        self.assertEqual(target.read_bytes(), b"outside bytes")

    def test_mutated_carrier_is_not_deleted_on_rollback(self):
        def corrupts_carrier(path, data):
            if path == self.view:
                self.carrier.write_bytes(b"external replacement")
                raise OSError("injected view failure")
            self.write_new(path, data)
        with self.assertRaisesRegex(OSError, "PAIR_ROLLBACK_BLOCKED"):
            self.publish(corrupts_carrier)
        self.assertEqual(self.carrier.read_bytes(), b"external replacement")



    def test_mismatched_stem_rejected_before_any_publication(self):
        other_view = self.root / "other"
        with self.assertRaisesRegex(ValueError, "PAIR_NONCANONICAL_SAME_STEM"):
            publisher.publish_pair(self.write_new, self.carrier, self.carrier_bytes,
                                   other_view, self.view_bytes)
        self.assertFalse(self.carrier.exists())
        self.assertFalse(other_view.exists())

    def test_non_sens_carrier_rejected_before_any_publication(self):
        wrong_carrier = self.root / "branch.bin"
        with self.assertRaisesRegex(ValueError, "PAIR_NONCANONICAL_SAME_STEM"):
            publisher.publish_pair(self.write_new, wrong_carrier, self.carrier_bytes,
                                   self.view, self.view_bytes)
        self.assertFalse(wrong_carrier.exists())
        self.assertFalse(self.view.exists())

    def test_same_bytes_replacement_is_not_deleted_during_rollback(self):
        # Use rename from a separately created inode, avoiding inode reuse
        # from unlink-then-create; replacement bytes intentionally match.
        def swaps_carrier_then_fails(path, data):
            if path == self.view:
                replacement = self.root / "replacement.sens"
                replacement.write_bytes(self.carrier_bytes)
                replacement.replace(self.carrier)
                raise OSError("injected view failure")
            self.write_new(path, data)

        with self.assertRaisesRegex(OSError, "PAIR_ROLLBACK_BLOCKED"):
            self.publish(swaps_carrier_then_fails)
        self.assertEqual(self.carrier.read_bytes(), self.carrier_bytes)
        self.assertFalse(self.view.exists())

if __name__ == "__main__":
    unittest.main()
