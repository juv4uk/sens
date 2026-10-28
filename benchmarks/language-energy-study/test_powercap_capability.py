#!/usr/bin/env python3
"""Synthetic falsification and real-host *accessibility* log for #6289.

No time-bracketed energy, conversion to joules, or SENS semantic laws.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("powercap_capability.py")
spec = importlib.util.spec_from_file_location("sens_powercap_capability", SCRIPT)
assert spec and spec.loader
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def package(root: Path, index: int, *, name: str = "package-0",
            energy: str | None = "120000", maximum: str | None = "200000") -> None:
    zone = root / f"intel-rapl:{index}"
    zone.mkdir(parents=True)
    (zone / "name").write_text(name + "\n", encoding="ascii")
    if energy is not None:
        (zone / "energy_uj").write_text(energy + "\n", encoding="ascii")
    if maximum is not None:
        (zone / "max_energy_range_uj").write_text(maximum + "\n", encoding="ascii")


def check_nonmeasurement(test: unittest.TestCase, report: dict) -> None:
    test.assertEqual(report["schema"], "sens-powercap-capability/v1")
    test.assertIn(report["status"], tool.STATUSES)
    test.assertEqual(report["energy_status"], "ENERGY_NOT_MEASURED")
    test.assertIsNone(report["energy_joules"])
    test.assertFalse(report["physical_calibration_verified"])
    test.assertEqual(report["scope"], "CPU_PACKAGE_NOT_PROCESS")


class PowercapCapabilityTests(unittest.TestCase):
    def test_missing_sysfs_is_explicit_hardware_access_blocker(self):
        with tempfile.TemporaryDirectory() as temp:
            report = tool.probe(Path(temp) / "missing", system_name="Linux")
            self.assertEqual(report["status"], "POWERCAP_SYSFS_MISSING")
            self.assertEqual(report["readable_package_counters"], [])
            check_nonmeasurement(self, report)

    def test_existing_but_empty_tree_is_no_package(self):
        with tempfile.TemporaryDirectory() as temp:
            report = tool.probe(Path(temp), system_name="Linux")
            self.assertEqual(report["status"], "NO_PACKAGE_ZONE")
            check_nonmeasurement(self, report)

    def test_foreign_os_is_not_claimed_to_lack_other_energy_sensors(self):
        for name in ("Windows", "Darwin"):
            with self.subTest(os=name):
                report = tool.probe(Path("/definitely-not-a-linux-sysfs"),
                                    system_name=name)
                self.assertEqual(report["status"], "LINUX_POWERCAP_NOT_APPLICABLE")
                check_nonmeasurement(self, report)

    def test_fake_readable_package_is_still_not_energy_measurement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package(root, 0)
            report = tool.probe(root, system_name="Linux")
            self.assertEqual(report["status"], "COUNTER_READABLE_UNCALIBRATED")
            self.assertEqual(report["readable_package_counters"], ["intel-rapl:0"])
            self.assertNotIn("120000", json.dumps(report))
            check_nonmeasurement(self, report)

    def test_no_accidental_child_subzone_admission(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package(root, 0, name="core")
            package(root, 1, name="dram")
            fake = root / "intel-rapl:0:0"
            fake.mkdir()
            (fake / "name").write_text("package-0\n", encoding="ascii")
            report = tool.probe(root, system_name="Linux")
            self.assertEqual(report["status"], "NO_PACKAGE_ZONE")
            check_nonmeasurement(self, report)

    def test_missing_or_corrupt_counter_does_not_become_joules(self):
        for energy, maximum in ((None, "1000"), ("123", None), ("bad", "123"),
                                ("2", "0"), ("2", "-50"), ("", "1000"),
                                ("2", "not-integer")):
            with self.subTest(energy=energy, max_range=maximum):
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    package(root, 0, energy=energy, maximum=maximum)
                    report = tool.probe(root, system_name="Linux")
                    self.assertEqual(report["status"], "COUNTER_MISSING_OR_UNREADABLE")
                    check_nonmeasurement(self, report)

    def test_two_readable_packages_are_not_silently_selected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package(root, 0, name="package-0")
            package(root, 1, name="package-1")
            report = tool.probe(root, system_name="Linux")
            self.assertEqual(report["status"],
                             "MULTIPLE_PACKAGE_COUNTERS_UNCALIBRATED")
            self.assertEqual(len(report["readable_package_counters"]), 2)
            check_nonmeasurement(self, report)

    def test_one_readable_one_unreadable_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package(root, 0, name="package-0")
            package(root, 1, name="package-1", energy=None)
            report = tool.probe(root, system_name="Linux")
            self.assertEqual(report["status"],
                             "MULTIPLE_PACKAGE_COUNTERS_UNCALIBRATED")
            check_nonmeasurement(self, report)

    def test_zero_counter_readout_does_not_imply_zero_energy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package(root, 0, energy="0", maximum="100")
            report = tool.probe(root, system_name="Linux")
            self.assertEqual(report["status"], "COUNTER_READABLE_UNCALIBRATED")
            self.assertIsNone(report["energy_joules"])

    def test_actual_runner_sensor_capability_is_logged_not_inferred(self):
        report = tool.probe()
        check_nonmeasurement(self, report)
        print("POWER_SENSOR_CAPABILITY " + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
