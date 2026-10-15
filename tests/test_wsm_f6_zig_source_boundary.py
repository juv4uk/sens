#!/usr/bin/env python3
"""Focused F6 host source isolation: Zig carries exact bytes; SENS keeps semantics.

Source guard only, with negative mutants; the same central CI compiles both Rust
binaries against the real linked Zig ABI. Never calls this semantic admission.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "crates/sens-cli/src/bin/wsm-fs-record-producer.rs",
    "crates/sens-cli/src/bin/wsm-fs-record-consumer.rs",
)
DIRECT = re.compile(r'include_(?:str|bytes)!\s*\(\s*"[^"]*/lib/(?:unify|reason|forward|knowledge)\.lisp"')

def check_f6_route(source: str, label: str) -> None:
    # Commented-out code cannot impersonate a live Zig route.
    live = re.sub(r"(?m)^\s*//[^\n]*$", "", source)
    if DIRECT.search(live):
        raise ValueError(f"F6_DIRECT_RUST_SOURCE layer=transport binary={label}")
    if '#[path = "../zig_transport.rs"]' not in live:
        raise ValueError(f"F6_NO_ZIG_MODULE layer=transport binary={label}")
    for asset in ("unify", "reason", "forward", "knowledge"):
        call = f"zig_transport::{asset}_source_bytes()?"
        if live.count(call) != 1:
            raise ValueError(f"F6_MISSING_ZIG_CARRIER layer=transport binary={label} asset={asset}")
    if '#[cfg(not(feature = "zig-transport"))]' not in live or "no Rust fallback" not in live:
        raise ValueError(f"F6_FALLBACK_UNSAFE layer=transport binary={label}")
    if "let sources = zig_bootstrap_sources()" not in live:
        raise ValueError(f"F6_MISSING_BOOTSTRAP layer=transport binary={label}")
    a = live.find('("lib/unify.lisp", sources[0].as_str())')
    b = live.find('("lib/reason.lisp", sources[1].as_str())')
    c = live.find('("lib/forward.lisp", sources[2].as_str())')
    d = live.find('("lib/knowledge.lisp", sources[3].as_str())')
    if a < 0 or b < 0 or c < 0 or d < 0 or not (a < b < c < d):
        raise ValueError(f"F6_ORDER_CHANGED layer=transport binary={label}")
    if "sens::eval_pinned_reasoning_source(path, source, &mut session)" not in live:
        raise ValueError(f"F6_NO_SENS_EVALUATOR layer=eval binary={label}")

class F6ZigBoundaryTests(unittest.TestCase):
    def test_both_real_bins_use_only_existing_zig_source_carriers(self) -> None:
        for file in FILES:
            with self.subTest(file=file):
                check_f6_route((ROOT / file).read_text(encoding="utf-8"), file)

    def test_direct_rust_embed_mutant_is_rejected(self) -> None:
        for file in FILES:
            source = (ROOT / file).read_text(encoding="utf-8")
            mutation = source + '\nconst SHADOW: &str = include_str!("../../../../lib/knowledge.lisp");\n'
            with self.subTest(file=file), self.assertRaisesRegex(ValueError, "F6_DIRECT_RUST_SOURCE"):
                check_f6_route(mutation, file)

    def test_zig_token_in_comment_cannot_replace_live_source_call(self) -> None:
        for file in FILES:
            source = (ROOT / file).read_text(encoding="utf-8")
            mutant = source.replace(
                "zig_transport::knowledge_source_bytes()?",
                "/* disabled */ missing_knowledge_source()?", 1,
            ) + "\n// zig_transport::knowledge_source_bytes()?\n"
            with self.subTest(file=file), self.assertRaisesRegex(ValueError, "F6_MISSING_ZIG_CARRIER"):
                check_f6_route(mutant, file)

    def test_swap_reason_and_forward_load_order_is_rejected(self) -> None:
        for file in FILES:
            source = (ROOT / file).read_text(encoding="utf-8")
            # Use a temporary sentinel to exchange two source positions.
            changed = source.replace(
                '("lib/reason.lisp", sources[1].as_str()),',
                '("__TEMP_ORDER_SENTINEL__", sources[1].as_str()),', 1,
            ).replace(
                '("lib/forward.lisp", sources[2].as_str()),',
                '("lib/reason.lisp", sources[1].as_str()),', 1,
            ).replace(
                '("__TEMP_ORDER_SENTINEL__", sources[1].as_str()),',
                '("lib/forward.lisp", sources[2].as_str()),', 1,
            )
            self.assertNotEqual(changed, source)
            with self.subTest(file=file), self.assertRaisesRegex(ValueError, "F6_ORDER_CHANGED"):
                check_f6_route(changed, file)

    def test_swap_forward_and_knowledge_order_is_rejected(self) -> None:
        for file in FILES:
            source = (ROOT / file).read_text(encoding="utf-8")
            changed = source.replace(
                '("lib/forward.lisp", sources[2].as_str()),',
                '("__ORDER_SENTINEL__", sources[2].as_str()),', 1,
            ).replace(
                '("lib/knowledge.lisp", sources[3].as_str()),',
                '("lib/forward.lisp", sources[2].as_str()),', 1,
            ).replace(
                '("__ORDER_SENTINEL__", sources[2].as_str()),',
                '("lib/knowledge.lisp", sources[3].as_str()),', 1,
            )
            self.assertNotEqual(changed, source)
            with self.subTest(file=file), self.assertRaisesRegex(ValueError, "F6_ORDER_CHANGED"):
                check_f6_route(changed, file)

    def test_no_zig_feature_must_refuse_instead_of_rust_fallback(self) -> None:
        for file in FILES:
            source = (ROOT / file).read_text(encoding="utf-8")
            mutant = source.replace("no Rust fallback\".into()", "host-side fallback\".into()", 1)
            with self.subTest(file=file), self.assertRaisesRegex(ValueError, "F6_FALLBACK_UNSAFE"):
                check_f6_route(mutant, file)

if __name__ == "__main__":
    unittest.main(verbosity=2)
