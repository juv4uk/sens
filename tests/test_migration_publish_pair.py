"""Narrow positive/negative controls for same-stem carrier/view publication."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

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
        self.view_bytes = b"10 110 00\\n"

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

    def test_mutated_carrier_is_not_deleted_on_rollback(self):
        def corrupts_carrier(path, data):
            if path == self.view:
                self.carrier.write_bytes(b"external replacement")
                raise OSError("injected view failure")
            self.write_new(path, data)
        with self.assertRaisesRegex(OSError, "PAIR_ROLLBACK_BLOCKED"):
            self.publish(corrupts_carrier)
        self.assertEqual(self.carrier.read_bytes(), b"external replacement")


if __name__ == "__main__":
    unittest.main()
