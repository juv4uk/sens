"""Zig 0.16.0 Cargo build-script environment change regression.

CI_GLUE_NO_SEMANTICS: verifies build provenance only, not SENS law.
Run: python3 -m unittest tests/test_zig_build_environment_watch.py -v
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "crates/sens-cli/build.rs"

WATCHES = (
    'println!("cargo:rerun-if-env-changed=ZIG");',
    'println!("cargo:rerun-if-env-changed=PATH");',
)


def check_environment_watches(source: str) -> None:
    branch = 'if env::var_os("CARGO_FEATURE_ZIG_TRANSPORT").is_none() {'
    marker = source.find(branch)
    if marker < 0:
        raise ValueError("ZIG_CORRIDOR_BUILD_FAIL layer=build missing=feature_switch")
    for watch in WATCHES:
        if source.count(watch) != 1 or source.index(watch) >= marker:
            raise ValueError(
                f"ZIG_CORRIDOR_BUILD_FAIL layer=build missing_or_late={watch}"
            )
    # This is deliberately an external compiler, not a Rust T5 fallback.
    for required in (
        'env::var_os("ZIG")',
        'include_str!("../../.zig-version")',
        '.arg("research/zig-codecs/transport_abi.zig")',
        'assert_eq!(actual, pinned,',
        'println!("cargo:rustc-link-lib=static=sens_zig_transport");',
    ):
        if required not in source:
            raise ValueError(
                f"ZIG_CORRIDOR_BUILD_FAIL layer=build missing={required}"
            )


class ZigBuildEnvironmentWatchTest(unittest.TestCase):
    def test_pinned_zig_compiler_choice_invalidates_cargo_archive(self) -> None:
        source = BUILD.read_text(encoding="utf-8")
        check_environment_watches(source)

        # Negative controls: each lost watch must fail for the right reason.
        for lost in WATCHES:
            with self.subTest(mutation=lost):
                mutated = source.replace(lost, "", 1)
                with self.assertRaisesRegex(ValueError, "missing_or_late"):
                    check_environment_watches(mutated)

        # Moving a directive behind an early return is also forbidden.
        moved = source.replace(WATCHES[0], "", 1).replace(
            '    let root = PathBuf::from(',
            '    ' + WATCHES[0] + '\n    let root = PathBuf::from(',
            1,
        )
        with self.assertRaisesRegex(ValueError, "missing_or_late"):
            check_environment_watches(moved)


if __name__ == "__main__":
    unittest.main()
