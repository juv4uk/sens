"""Fail-closed release preflight trigger scope regression for main-only integration.

Do not allow edits to the Guix version, tag driver, or package installer to
silently bypass release-preflight.yml. The tagged release still performs the
complete, independent strict checks before publication.
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "release-preflight.yml"

REQUIRED = (
    "rust-toolchain.toml",
    "Cargo.lock",
    "Cargo.toml",
    "crates/**/Cargo.toml",
    "lib/core4.lisp",
    "lib/time.lisp",
    "lib/machine/**",
    "crates/sens/src/mixed_source.rs",
    "crates/sens/src/eval/**",
    "crates/sens/src/frame3_micro*.rs",
    "crates/sens/tests/timezone_raw.rs",
    "crates/sens-host/tests/native_cond_profile.rs",
    "crates/sens-host/tests/native_lisp_bytes.rs",
    "scripts/check_d3_legacy_logic.py",
    "tests/test_d3_legacy_logic_guard.py",
    "guix.scm",
    "scripts/release.lisp",
    "scripts/verify_release_tag.py",
    "scripts/verify_release_assets.py",
    "packaging/**",
    "tests/test_verify_release_assets.py",
    "tests/test_verify_release_ci.py",
    ".github/workflows/release-preflight.yml",
    ".github/workflows/release.yml",
)


def require_trigger_coverage(source: str) -> None:
    """Raise when either push-to-main or PR event loses release-related paths."""
    try:
        events = source.split("\non:\n", 1)[1].split("\nconcurrency:", 1)[0]
        push = events.split("  push:\n", 1)[1].split("  pull_request:\n", 1)[0]
        pull = events.split("  pull_request:\n", 1)[1].split("  workflow_dispatch:", 1)[0]
    except IndexError as exc:
        raise AssertionError("RELEASE_BLOCKED: preflight trigger structure missing") from exc

    if "    branches: [main]\n" not in push:
        raise AssertionError("RELEASE_BLOCKED: main push is not checked")
    for label, block in (("push", push), ("pull_request", pull)):
        if "    paths:\n" not in block:
            raise AssertionError(f"RELEASE_BLOCKED: {label} path allowlist missing")
        for item in REQUIRED:
            if f'      - "{item}"\n' not in block:
                raise AssertionError(f"RELEASE_BLOCKED: {label} excludes {item}")
    if "  workflow_dispatch:\n" not in events:
        raise AssertionError("RELEASE_BLOCKED: explicit manual preflight unavailable")


class ReleasePreflightScopeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_critical_release_paths_trigger_preflight(self):
        require_trigger_coverage(self.workflow)

    def test_negative_guard_rejects_missing_guix_change(self):
        corrupted = self.workflow.replace('      - "guix.scm"\n', "", 1)
        with self.assertRaisesRegex(AssertionError, "excludes guix.scm"):
            require_trigger_coverage(corrupted)

    def test_negative_guard_rejects_missing_time_and_native_semantic_paths(self):
        for path in ("lib/time.lisp", "crates/sens/src/mixed_source.rs",
                     "crates/sens-host/tests/native_lisp_bytes.rs"):
            with self.subTest(path=path):
                corrupted = self.workflow.replace(f'      - "{path}"\n', "", 1)
                with self.assertRaisesRegex(AssertionError, "excludes "):
                    require_trigger_coverage(corrupted)

    def test_negative_guard_rejects_missing_installer_scope(self):
        prefix, suffix = self.workflow.split("  pull_request:\n", 1)
        corrupted = prefix + "  pull_request:\n" + suffix.replace(
            '      - "packaging/**"\n', "", 1
        )
        with self.assertRaisesRegex(AssertionError, "excludes packaging/"):
            require_trigger_coverage(corrupted)


if __name__ == "__main__":
    unittest.main()
