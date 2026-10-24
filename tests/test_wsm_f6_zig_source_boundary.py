#!/usr/bin/env python3
"""F6 executables use the aggregate Core4 T5M bootstrap, without module includes."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINS = (
    "crates/sens-cli/src/bin/wsm-fs-record-producer.rs",
    "crates/sens-cli/src/bin/wsm-fs-record-consumer.rs",
)
def live_source(source: str) -> str:
    return re.sub(r"(?m)^\s*//[^\n]*$", "", source)


def check_bin(source: str, label: str) -> None:
    live = live_source(source)
    if "load_core_library(&mut session)" not in live:
        raise ValueError(f"F6_MISSING_CORE4_BOOTSTRAP binary={label}")
    for forbidden in (
        "bootstrap_f6_libraries",
        "zig_bootstrap_sources",
        "String::from_utf8",
        "eval_pinned_reasoning_source",
        "include_str!(\"../../../../lib/",
    ):
        if forbidden in live:
            raise ValueError(f"F6_SEPARATE_SOURCE_INGRESS binary={label} symbol={forbidden}")


def check_core4_bootstrap(build: str, zig: str, rust: str) -> None:
    watch = '"lib/core4.sens"'
    if watch not in build or watch not in zig:
        raise ValueError("F6_CORE4_T5M_NOT_THE_WATCHED_PHYSICAL_BOOTSTRAP")
    if "t5m.decode" not in zig or "CORE4_BOOTSTRAP_WORDS" not in zig:
        raise ValueError("F6_CORE4_NOT_DECODED_BY_PINNED_ZIG_T5M")
    if "PhysicalT5Program::from_exact_domain_words_owned" not in rust:
        raise ValueError("F6_CORE4_WORDS_NOT_GIVEN_TO_SENS_BINARY_READER")


class F6Core4BoundaryTests(unittest.TestCase):
    def test_both_bins_use_the_shared_physical_bootstrap(self) -> None:
        for path in BINS:
            with self.subTest(path=path):
                check_bin((ROOT / path).read_text(encoding="utf-8"), path)

    def test_f6_uses_the_physical_aggregate_core4_bootstrap(self) -> None:
        check_core4_bootstrap(
            (ROOT / "crates/sens/build.rs").read_text(encoding="utf-8"),
            (ROOT / "bootstrap_t5m.zig").read_text(encoding="utf-8"),
            (ROOT / "crates/sens/src/binary_bootstrap.rs").read_text(encoding="utf-8"),
        )

    def test_text_ingress_mutant_is_rejected(self) -> None:
        source = (ROOT / BINS[0]).read_text(encoding="utf-8")
        mutant = source.replace(
            "load_core_library(&mut session)",
            "load_core_library(&mut session);\n    let _ = String::from_utf8(vec![])",
            1,
        )
        with self.assertRaisesRegex(ValueError, "F6_SEPARATE_SOURCE_INGRESS"):
            check_bin(mutant, BINS[0])

    def test_missing_bootstrap_call_is_rejected(self) -> None:
        source = (ROOT / BINS[1]).read_text(encoding="utf-8")
        mutant = source.replace("load_core_library(&mut session)", "Ok(())", 1)
        with self.assertRaisesRegex(ValueError, "F6_MISSING_CORE4_BOOTSTRAP"):
            check_bin(mutant, BINS[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
